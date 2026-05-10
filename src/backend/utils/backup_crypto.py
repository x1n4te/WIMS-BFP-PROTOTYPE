"""
Backup encryption using AES-256-GCM — same key management as PII encryption.

Encrypted backup format (binary):
    [12-byte nonce][N-byte ciphertext+tag]  (raw concatenation)

File extension: .sql.enc
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BACKUP_KEY_ENV = "WIMS_MASTER_KEY"
BACKUP_NONCE_BYTES = 12


def _get_backup_key() -> bytes:
    raw = os.environ.get(BACKUP_KEY_ENV)
    if not raw:
        raise RuntimeError(f"Required env var {BACKUP_KEY_ENV!r} is not set")
    try:
        key_bytes = base64.b64decode(raw)
    except Exception as e:
        raise RuntimeError(f"{BACKUP_KEY_ENV!r} is not valid base64: {e}")
    if len(key_bytes) != 32:
        raise RuntimeError(f"{BACKUP_KEY_ENV!r} must be 32 bytes for AES-256")
    return key_bytes


def encrypt_backup(input_path: Path, output_path: Path | None = None) -> Path:
    """
    Encrypt a backup file with AES-256-GCM and write to output_path.

    Args:
        input_path:  Path to the raw (unencrypted) backup .sql file.
        output_path:  Optional output path. Defaults to input_path.with_suffix('.sql.enc').
                      If output_path equals input_path (in-place), the raw file is replaced.

    Returns:
        Path to the encrypted .sql.enc file.
    """
    key = _get_backup_key()
    aesgcm = AESGCM(key)

    data = input_path.read_bytes()
    nonce = os.urandom(BACKUP_NONCE_BYTES)
    ciphertext = aesgcm.encrypt(nonce, data, None)  # no AAD for backup files

    out = output_path or input_path.with_suffix(".sql.enc")
    out.write_bytes(nonce + ciphertext)

    # Remove raw file after successful encryption (in-place replacement)
    if input_path.exists() and (output_path is None or output_path == input_path):
        input_path.unlink()
    elif output_path and output_path != input_path:
        input_path.unlink()

    return out


def decrypt_backup(encrypted_path: Path, output_path: Path | None = None) -> Path:
    """
    Decrypt an AES-256-GCM encrypted backup file.

    Args:
        encrypted_path:  Path to the .sql.enc encrypted backup.
        output_path:     Optional output path. Defaults to encrypted_path.with_suffix('.sql').
                         If output_path equals encrypted_path (in-place), the .enc file is replaced.

    Returns:
        Path to the decrypted .sql file.
    """
    key = _get_backup_key()
    aesgcm = AESGCM(key)

    data = encrypted_path.read_bytes()
    if len(data) < BACKUP_NONCE_BYTES:
        raise RuntimeError("Encrypted backup file too short to contain nonce")

    nonce = data[:BACKUP_NONCE_BYTES]
    ciphertext = data[BACKUP_NONCE_BYTES:]

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        raise RuntimeError(f"Decryption failed (wrong key or tampered file): {e}")

    out = output_path or encrypted_path.with_suffix(".sql")

    if output_path and output_path != encrypted_path:
        # Write to temp then replace to avoid partial writes
        tmp = encrypted_path.with_suffix(".sql.tmp")
        tmp.write_bytes(plaintext)
        tmp.replace(output_path)
        encrypted_path.unlink()
    else:
        # In-place: write to .sql directly
        out.write_bytes(plaintext)
        encrypted_path.unlink()

    return out
