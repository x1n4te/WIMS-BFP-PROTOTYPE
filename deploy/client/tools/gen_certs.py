"""Create (or reuse) the WIMS local CA and issue a server certificate.

usage: gen_certs.py <out_dir> <hostname> <server_ip> [<extra_ip> ...]

Output layout:
  <out_dir>/ca/ca.crt, ca.key        CA certificate (give ca.crt to every office PC) and key
  <out_dir>/server/server.crt, .key  leaf certificate for <hostname> + the IPs, signed by the CA

The CA is reused when it already exists, so re-issuing the server certificate (new IP, expiry)
does not require reinstalling the CA on office PCs. Runs inside wims-backend:client (it ships
the `cryptography` package), so the host needs neither openssl nor Python.
"""

import datetime
import ipaddress
import os
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

CA_DAYS = 3650
SERVER_DAYS = 825  # keep below the 825-day limit some platforms enforce


def _write(path, data, mode=0o644):
    with open(path, "wb") as fh:
        fh.write(data)
    os.chmod(path, mode)


def _key_pem(key):
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _name(common_name):
    return x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WIMS-BFP"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )


def load_or_create_ca(ca_dir):
    crt_path, key_path = os.path.join(ca_dir, "ca.crt"), os.path.join(ca_dir, "ca.key")
    if os.path.exists(crt_path) and os.path.exists(key_path):
        with open(crt_path, "rb") as fh:
            cert = x509.load_pem_x509_certificate(fh.read())
        with open(key_path, "rb") as fh:
            key = serialization.load_pem_private_key(fh.read(), password=None)
        print("reusing existing CA")
        return cert, key
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(_name("WIMS-BFP Local CA"))
        .issuer_name(_name("WIMS-BFP Local CA"))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=CA_DAYS))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .sign(key, hashes.SHA256())
    )
    _write(crt_path, cert.public_bytes(serialization.Encoding.PEM))
    _write(key_path, _key_pem(key), 0o600)
    print("created new CA")
    return cert, key


def issue_server_cert(ca_cert, ca_key, host, ips, server_dir):
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.datetime.now(datetime.UTC)
    san = [x509.DNSName(host)] + [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips]
    cert = (
        x509.CertificateBuilder()
        .subject_name(_name(host))
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=SERVER_DAYS))
        .add_extension(x509.SubjectAlternativeName(san), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    chain = cert.public_bytes(serialization.Encoding.PEM) + ca_cert.public_bytes(
        serialization.Encoding.PEM
    )
    _write(os.path.join(server_dir, "server.crt"), chain)
    # nginx runs as an unprivileged user inside the container and reads this through a
    # read-only bind mount, so the key must be world-readable on the host copy.
    _write(os.path.join(server_dir, "server.key"), _key_pem(key), 0o644)
    return cert


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    out_dir, host, *ips = sys.argv[1:]
    ca_dir, server_dir = os.path.join(out_dir, "ca"), os.path.join(out_dir, "server")
    os.makedirs(ca_dir, exist_ok=True)
    os.makedirs(server_dir, exist_ok=True)
    ca_cert, ca_key = load_or_create_ca(ca_dir)
    cert = issue_server_cert(ca_cert, ca_key, host, ips, server_dir)
    print(f"server certificate for {host} {ips} valid until {cert.not_valid_after_utc:%Y-%m-%d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
