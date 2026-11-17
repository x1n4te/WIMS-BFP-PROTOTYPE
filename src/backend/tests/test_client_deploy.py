"""Static guards for the client deployment package (deploy/client/).

None of this needs Docker or a database: it checks that the package files are consistent with
each other and with the repository (include list vs. postgres-init, compose vs. removed
services, secrets generated vs. secrets required, nginx hardening, dev/demo data split).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import pathlib
import re
import sys

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[3]
CLIENT = REPO / "deploy" / "client"
INIT_SRC = REPO / "src" / "postgres-init"

DEV_DEMO_FILES = {
    "03a_dev_users.sql",
    "14a_assign_ncr_to_test_users.sql",
    "14b_assign_ncr_to_team_accounts.sql",
    "29_seed_incidents.sql",
    "38_seed_security_threat_logs.sql",
}
REMOVED = ("openbao", "suricata", "ollama", "osrm", "mailhog", "turnstile", "firebase")

pytestmark = pytest.mark.skipif(not CLIENT.is_dir(), reason="deploy/client not present")


def _include_list() -> list[str]:
    lines = (CLIENT / "init-files.txt").read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def _compose() -> dict:
    return yaml.safe_load((CLIENT / "docker-compose.yml").read_text(encoding="utf-8"))


# ── Clean data ─────────────────────────────────────────────────────────────────────────


def test_include_list_files_exist_and_are_sorted():
    listed = _include_list()
    assert listed == sorted(listed)
    for name in listed:
        assert (INIT_SRC / name).is_file(), name


def test_include_list_excludes_every_dev_and_demo_file():
    assert not DEV_DEMO_FILES & set(_include_list())


def test_every_init_file_is_classified():
    on_disk = {p.name for p in INIT_SRC.glob("*.sql")}
    unclassified = on_disk - set(_include_list()) - DEV_DEMO_FILES
    assert not unclassified, f"classify in deploy/client/init-files.txt: {sorted(unclassified)}"


def test_dev_files_are_listed_as_excluded_in_the_header():
    header = "\n".join(
        ln
        for ln in (CLIENT / "init-files.txt").read_text(encoding="utf-8").splitlines()
        if ln.lstrip().startswith("#")
    )
    for name in DEV_DEMO_FILES:
        assert name in header


def test_users_file_split_keeps_service_accounts_only():
    shared = (INIT_SRC / "03_users.sql").read_text(encoding="utf-8")
    dev = (INIT_SRC / "03a_dev_users.sql").read_text(encoding="utf-8")
    assert "svc_task" in shared and "CREATE TABLE IF NOT EXISTS wims.users" in shared
    for username in (
        "encoder_ncr",
        "validator_test",
        "analyst_test",
        "admin_test",
        "n-val",
        "r-sys",
    ):
        assert f"'{username}'" not in shared
        assert f"'{username}'" in dev


def test_dev_users_sort_between_03_and_04():
    names = sorted(p.name for p in INIT_SRC.glob("*.sql"))
    i = names.index("03_users.sql")
    assert names[i + 1] == "03a_dev_users.sql"
    assert names[i + 2].startswith("04_")


def test_no_client_init_file_inserts_dev_or_demo_rows():
    dev_markers = ("encoder_ncr", "validator_test", "INSERT INTO wims.fire_incidents (")
    for name in _include_list():
        text = (INIT_SRC / name).read_text(encoding="utf-8")
        for marker in dev_markers:
            if marker == "INSERT INTO wims.fire_incidents (":
                # only the audit trigger function (63) writes incident-shaped rows, to audit
                assert marker not in text, (name, marker)
            elif name not in ("15_validator_workflow.sql", "21_all_regions.sql"):
                # these two only UPDATE rows of dev users that are absent on clients (no-op)
                assert marker not in text, (name, marker)


def test_init_extra_password_script_is_executable_and_alphanumeric_guarded():
    script = CLIENT / "init-extra" / "zz_client_set_passwords.sh"
    assert os.access(script, os.X_OK)
    text = script.read_text(encoding="utf-8")
    assert "ALTER ROLE keycloak PASSWORD" in text and "ALTER ROLE wims_app_user PASSWORD" in text
    assert "[!A-Za-z0-9]" in text
    # must sort after every SQL file
    assert script.name > max(p.name for p in INIT_SRC.glob("*.sql"))


# ── Compose ────────────────────────────────────────────────────────────────────────────


def test_compose_services_and_no_removed_references():
    compose = _compose()
    assert set(compose["services"]) == {
        "postgres",
        "redis",
        "keycloak",
        "backend",
        "celery-worker",
        "frontend",
        "nginx",
    }
    raw = (CLIENT / "docker-compose.yml").read_text(encoding="utf-8").lower()
    # comments may say what is NOT included; strip them
    code = "\n".join(ln.split("#", 1)[0] for ln in raw.splitlines())
    for word in REMOVED:
        assert word not in code, word
    assert "extra_hosts" not in code


def test_compose_depends_on_targets_exist_and_policies():
    compose = _compose()
    services = compose["services"]
    for name, svc in services.items():
        deps = svc.get("depends_on") or {}
        for target in deps:
            assert target in services, (name, target)
        assert svc.get("restart") == "unless-stopped", name
        assert svc.get("mem_limit"), name
        assert svc.get("logging", {}).get("options", {}).get("max-size"), name


def test_only_nginx_publishes_ports_80_and_443():
    services = _compose()["services"]
    for name, svc in services.items():
        if name == "nginx":
            assert sorted(svc["ports"]) == ["443:443", "80:80"]
        else:
            assert "ports" not in svc, name


def test_memory_budget_fits_the_wsl_cap():
    def mib(v: str) -> int:
        assert v.endswith("m")
        return int(v[:-1])

    total = sum(mib(s["mem_limit"]) for s in _compose()["services"].values())
    assert total <= 3072, total  # leaves >= 1 GB of the 4 GB WSL2 cap for kernel/page cache
    env = _compose()["services"]["keycloak"]["environment"]
    assert "-Xmx448m" in env["JAVA_OPTS_KC_HEAP"]


def test_backend_and_worker_sized_for_low_cpu():
    services = _compose()["services"]
    assert "--workers" in services["backend"]["command"]
    cmd = services["backend"]["command"]
    assert cmd[cmd.index("--workers") + 1] == "1"
    assert "--beat" in services["celery-worker"]["command"]
    assert "--concurrency=2" in services["celery-worker"]["command"]


def test_crypto_provider_and_hostname_wiring():
    services = _compose()["services"]
    for name in ("backend", "celery-worker"):
        env = services[name]["environment"]
        assert env["WIMS_CRYPTO_PROVIDER"] == "env_aesgcm"
        assert "WIMS_MASTER_KEY" in env
    assert services["celery-worker"]["environment"]["WIMS_KMS_ROTATION_ENABLED"] == "false"
    host = "${WIMS_HOST:-wims.bfp.lan}"
    assert (
        services["backend"]["environment"]["KEYCLOAK_ISSUER"] == f"https://{host}/auth/realms/bfp"
    )
    assert services["keycloak"]["environment"]["KC_HOSTNAME"] == f"https://{host}/auth"
    fe = services["frontend"]["environment"]
    assert fe["NEXT_PUBLIC_BASE_URL"] == f"https://{host}"
    assert fe["NEXT_PUBLIC_OIDC_AUTHORITY"] == f"https://{host}/auth/realms/bfp"
    # build args must carry the same values as the runtime copies
    build = yaml.safe_load((CLIENT / "docker-compose.build.yml").read_text(encoding="utf-8"))
    args = build["services"]["frontend"]["build"]["args"]
    for key, value in args.items():
        assert fe[key] == value, key


def test_every_required_variable_is_generated_by_setup_secrets():
    raw = (CLIENT / "docker-compose.yml").read_text(encoding="utf-8")
    required = set(re.findall(r"\$\{([A-Z0-9_]+):\?", raw))
    generated = (CLIENT / "setup-secrets.ps1").read_text(encoding="utf-8")
    assert required, "expected required variables"
    for var in required:
        assert re.search(rf"^\s*{var}\s*=", generated, re.M), var
    with_defaults = set(re.findall(r"\$\{([A-Z0-9_]+):-", raw)) | required
    documented = (CLIENT / ".env.example").read_text(encoding="utf-8")
    for var in with_defaults:
        assert var in documented, f"{var} missing from .env.example"


def test_compose_mounts_exist_in_the_package():
    raw = _compose()
    for name, svc in raw["services"].items():
        for vol in svc.get("volumes", []):
            src = vol.split(":", 1)[0]
            if src.startswith("./"):
                top = src[2:].split("/", 1)[0]
                generated = {"postgres-init", "runtime", "certs"}
                assert top in generated or (CLIENT / top).exists(), (name, vol)


# ── nginx ──────────────────────────────────────────────────────────────────────────────────


def test_nginx_is_hardened_and_has_no_public_intake():
    conf = (CLIENT / "nginx.conf").read_text(encoding="utf-8")
    code = "\n".join(ln.split("#", 1)[0] for ln in conf.splitlines())
    assert "ssl_protocols       TLSv1.3;" in code
    assert "TLSv1.2" not in code and "TLSv1.1" not in code
    assert "Strict-Transport-Security" in code
    assert "wims.bfp.lan" in code and "192.168.1.50" in code
    for word in (
        "civilian",
        "turnstile",
        "cloudflare",
        "/api/v1/public",
        "wimsbfp.tech",
        "gstatic",
    ):
        assert word not in code.lower(), word
    assert "return 301 https://" in code
    assert "location = /api/events/stream" in code and "proxy_buffering off" in code


# ── Python tools ──────────────────────────────────────────────────────────────────────────────


def _load_tool(name: str):
    spec = importlib.util.spec_from_file_location(name, CLIENT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_render_realm_pins_redirects_to_the_client_host_and_drops_users():
    realm = json.loads((REPO / "src" / "keycloak" / "import" / "bfp-realm.json").read_text("utf-8"))
    out = _load_tool("render_realm").render(realm, "wims.example.lan")
    for client in out["clients"]:
        if client["clientId"] in ("wims-web", "bfp-client"):
            assert client["redirectUris"] == [
                "https://wims.example.lan/callback",
                "https://wims.example.lan/*",
            ]
            assert client["webOrigins"] == ["https://wims.example.lan"]
    blob = json.dumps(out)
    for stale in ("localhost", "wimsbfp.tech", "wims.bfp.gov.ph"):
        assert stale not in json.dumps(
            [c for c in out["clients"] if c["clientId"] in ("wims-web", "bfp-client")]
        )
    assert out["users"] == [] and blob


def test_gen_certs_issues_a_chain_for_host_and_ip(tmp_path):
    from cryptography import x509
    from cryptography.x509.oid import ExtensionOID

    tool = _load_tool("gen_certs")
    ca_dir, server_dir = tmp_path / "ca", tmp_path / "server"
    ca_dir.mkdir()
    server_dir.mkdir()
    ca_cert, ca_key = tool.load_or_create_ca(str(ca_dir))
    tool.issue_server_cert(ca_cert, ca_key, "wims.bfp.lan", ["192.168.1.50"], str(server_dir))
    leaf = x509.load_pem_x509_certificates((server_dir / "server.crt").read_bytes())[0]
    san = leaf.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value
    assert san.get_values_for_type(x509.DNSName) == ["wims.bfp.lan"]
    assert [str(i) for i in san.get_values_for_type(x509.IPAddress)] == ["192.168.1.50"]
    leaf.verify_directly_issued_by(ca_cert)
    # re-issuing must reuse the CA so office PCs need nothing new
    ca_again, _ = tool.load_or_create_ca(str(ca_dir))
    assert ca_again.fingerprint(ca_cert.signature_hash_algorithm) == ca_cert.fingerprint(
        ca_cert.signature_hash_algorithm
    )


# ── PowerShell scripts (static only: they cannot be executed on this platform) ──────────────────


PS_SCRIPTS = [
    "common",
    "setup-secrets",
    "setup-certs",
    "install",
    "backup",
    "restore",
    "build-bundle",
    "schedule-backup",
    "install-ca-office-pc",
]


@pytest.mark.parametrize("name", PS_SCRIPTS)
def test_powershell_script_is_ps51_compatible_and_balanced(name):
    path = CLIENT / f"{name}.ps1"
    text = path.read_text(encoding="utf-8")
    assert not text.startswith("\ufeff")
    # strip comment-based help and comment lines, then string literals, before counting brackets
    code = re.sub(r"<#.*?#>", "", text, flags=re.S)
    code = "\n".join(ln for ln in code.splitlines() if not ln.lstrip().startswith("#"))
    # one left-to-right pass so an apostrophe inside "..." is not mistaken for a '...' delimiter
    string_literal = re.compile("'(?:[^']|'')*'" + '|"(?:`.|[^"`])*"')
    stripped = string_literal.sub('""', code)
    for open_, close in ("{}", "()", "[]"):
        assert stripped.count(open_) == stripped.count(close), (name, open_)
    # operators that only exist in PowerShell 7
    assert " && " not in stripped and " || " not in stripped
    assert " ?? " not in stripped and not re.search(r"\?\s.+\s:\s", stripped)
    if name != "common" and name != "install-ca-office-pc":
        assert 'common.ps1"' in text


def test_install_script_wires_every_step():
    text = (CLIENT / "install.ps1").read_text(encoding="utf-8")
    for needle in (
        "SHA256SUMS.txt",
        "'load', '-i'",
        "setup-certs.ps1",
        "render_realm.py",
        "'--pull', 'never'",
        "Wait-ContainersReady",
        "bootstrap_admin.py",
        "backup.ps1",
    ):
        assert needle in text, needle


# ── KMS rotation switch ──────────────────────────────────────────────────────────────────────────


def _beat_schedule(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("WIMS_KMS_ROTATION_ENABLED", raising=False)
    else:
        monkeypatch.setenv("WIMS_KMS_ROTATION_ENABLED", value)
    sys.modules.pop("celery_config", None)
    return importlib.import_module("celery_config").celery_app.conf.beat_schedule


def test_kms_rotation_is_scheduled_by_default_and_off_for_clients(monkeypatch):
    try:
        assert "ensure-pii-key-rotation-daily" in _beat_schedule(monkeypatch, None)
        assert "ensure-pii-key-rotation-daily" not in _beat_schedule(monkeypatch, "false")
        assert "enforce-password-expiry-daily" in _beat_schedule(monkeypatch, "false")
    finally:
        monkeypatch.delenv("WIMS_KMS_ROTATION_ENABLED", raising=False)
        sys.modules.pop("celery_config", None)
        importlib.import_module("celery_config")
