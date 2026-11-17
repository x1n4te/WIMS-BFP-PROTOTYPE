"""Create the first SYSTEM_ADMIN (Keycloak user + wims.users row) on a fresh client install.

Port of scripts/bootstrap-admin.sh for hosts without bash: it runs inside the wims-backend
image (python, requests, sqlalchemy) on the compose network, so the host needs nothing.

Idempotent. The account gets UPDATE_PASSWORD and CONFIGURE_TOTP required actions with a
TEMPORARY password, so the first login forces a password change and OTP enrolment.
If the Keycloak user already exists its password is NOT reset; only the SYSTEM_ADMIN role and
the wims.users row are re-asserted.

Environment:
  KEYCLOAK_URL                 default http://keycloak:8080/auth (backchannel)
  KEYCLOAK_ADMIN_USER / KEYCLOAK_ADMIN_PASSWORD   master-realm admin (from .env)
  WIMS_HOST                    public hostname (forwarded-host header; default wims.bfp.lan)
  DATABASE_ADMIN_URL           postgres superuser URL (already set on the backend service)
  BOOTSTRAP_ADMIN_USERNAME / _EMAIL / _PASSWORD   required; _FIRST_NAME / _LAST_NAME optional
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import secrets
import sys
import time
from urllib.parse import quote

import requests
from sqlalchemy import create_engine, text

REALM = "bfp"
USERNAME_RE = re.compile(r"^[A-Za-z0-9._@-]{3,255}$")
EMAIL_RE = re.compile(r"^[^@\s']+@[^@\s']+$")


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        sys.exit(f"ERROR: {name} is required")
    return value


KC = os.environ.get("KEYCLOAK_URL", "http://keycloak:8080/auth").rstrip("/")
HOST = os.environ.get("WIMS_HOST", "wims.bfp.lan")
PUBLIC = f"https://{HOST}/auth"
# Keycloak is configured with a fixed https public URL and trusts X-Forwarded-*. Talk to it
# over the internal http address but present the same headers nginx does.
FWD = {
    "X-Forwarded-Proto": "https",
    "X-Forwarded-Host": HOST,
    "X-Forwarded-Port": "443",
}


def wait_for_keycloak(timeout: int = 240) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(f"{KC}/realms/{REALM}", headers=FWD, timeout=5).status_code == 200:
                print("Keycloak realm is up.")
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    sys.exit(f"ERROR: Keycloak realm '{REALM}' not reachable within {timeout}s")


def _form_action(html: str) -> str | None:
    m = re.search(r'action="([^"]*)"', html)
    if not m:
        return None
    action = m.group(1).replace("&amp;", "&")
    # Form actions carry the public https URL; the container reaches Keycloak internally.
    return action.replace(PUBLIC, KC, 1)


def complete_admin_profile(admin_user: str, admin_pass: str) -> None:
    """Keycloak 26's temporary bootstrap admin cannot use the password grant until the one-time
    VERIFY_PROFILE required action is resolved through the browser flow. Do that here.
    No-op when the admin is already permanent."""
    jar: dict[str, str] = {}

    def call(method: str, url: str, **kw):
        headers = dict(FWD)
        if jar:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in jar.items())
        r = requests.request(method, url, headers=headers, allow_redirects=False, timeout=15, **kw)
        for c in r.cookies:
            jar[c.name] = c.value
        return r

    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=")
    redirect_uri = quote(f"{PUBLIC}/admin/master/console/", safe="")
    page = call(
        "GET",
        f"{KC}/realms/master/protocol/openid-connect/auth?client_id=security-admin-console"
        f"&redirect_uri={redirect_uri}&response_type=code&scope=openid"
        f"&code_challenge={challenge.decode()}&code_challenge_method=S256",
    )
    action = _form_action(page.text)
    if not action:
        return
    r = call("POST", action, data={"username": admin_user, "password": admin_pass})
    location = r.headers.get("Location", "")
    if "required-action" in location and "VERIFY_PROFILE" in location:
        print("Completing one-time Keycloak admin profile setup (temporary bootstrap admin)...")
        location = location.replace(PUBLIC, KC, 1)
        form = call("GET", location)
        verify_action = _form_action(form.text)
        if verify_action:
            call(
                "POST",
                verify_action,
                data={
                    "email": f"admin@{HOST}",
                    "firstName": "System",
                    "lastName": "Admin",
                },
            )


def admin_token(admin_user: str, admin_pass: str) -> str:
    r = requests.post(
        f"{KC}/realms/master/protocol/openid-connect/token",
        headers=FWD,
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": admin_user,
            "password": admin_pass,
        },
        timeout=15,
    )
    if r.status_code != 200:
        sys.exit(
            f"ERROR: Keycloak admin login failed ({r.status_code}): {r.text[:300]}\n"
            f"Fallback: open https://{HOST}/auth/admin, sign in as '{admin_user}', complete the "
            "profile prompt, then run install.ps1 again."
        )
    return r.json()["access_token"]


def main() -> int:
    username = env("BOOTSTRAP_ADMIN_USERNAME")
    email = env("BOOTSTRAP_ADMIN_EMAIL")
    password = env("BOOTSTRAP_ADMIN_PASSWORD")
    first = os.environ.get("BOOTSTRAP_ADMIN_FIRST_NAME", "System")
    last = os.environ.get("BOOTSTRAP_ADMIN_LAST_NAME", "Administrator")
    if not USERNAME_RE.match(username):
        sys.exit("ERROR: username may only contain letters, digits, . _ @ - (3+ chars)")
    if not EMAIL_RE.match(email):
        sys.exit("ERROR: email is not a valid address")

    admin_user = env("KEYCLOAK_ADMIN_USER")
    admin_pass = env("KEYCLOAK_ADMIN_PASSWORD")

    wait_for_keycloak()
    complete_admin_profile(admin_user, admin_pass)
    api = f"{KC}/admin/realms/{REALM}"
    headers = {**FWD, "Authorization": f"Bearer {admin_token(admin_user, admin_pass)}"}

    def find_user_id() -> str | None:
        r = requests.get(
            f"{api}/users",
            params={"username": username, "exact": "true"},
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        users = r.json()
        return users[0]["id"] if users else None

    uid = find_user_id()
    if uid:
        print(f"Keycloak user '{username}' already exists ({uid}); password left unchanged.")
    else:
        print(f"Creating Keycloak user '{username}'...")
        r = requests.post(
            f"{api}/users",
            headers=headers,
            timeout=15,
            json={
                "username": username,
                "email": email,
                "firstName": first,
                "lastName": last,
                "enabled": True,
                "emailVerified": True,
                "requiredActions": ["UPDATE_PASSWORD", "CONFIGURE_TOTP"],
            },
        )
        if r.status_code != 201:
            sys.exit(f"ERROR: user creation failed ({r.status_code}): {r.text[:300]}")
        uid = find_user_id()
        if not uid:
            sys.exit("ERROR: user was created but its id could not be read")
        r = requests.put(
            f"{api}/users/{uid}/reset-password",
            headers=headers,
            timeout=15,
            json={"type": "password", "value": password, "temporary": True},
        )
        if r.status_code >= 300:
            requests.delete(f"{api}/users/{uid}", headers=headers, timeout=15)
            sys.exit(
                f"ERROR: initial password rejected ({r.status_code}: {r.text[:200]}). "
                "It must satisfy the realm policy (12+ chars, upper, lower, digit, special). "
                "The half-created user was removed."
            )

    print("Assigning SYSTEM_ADMIN...")
    role = requests.get(f"{api}/roles/SYSTEM_ADMIN", headers=headers, timeout=15)
    role.raise_for_status()
    requests.post(
        f"{api}/users/{uid}/role-mappings/realm",
        headers=headers,
        timeout=15,
        json=[role.json()],
    ).raise_for_status()

    print("Syncing wims.users...")
    engine = create_engine(env("DATABASE_ADMIN_URL"))
    with engine.begin() as conn:
        params = {"uid": uid, "username": username}
        conn.execute(
            text(
                "UPDATE wims.users SET keycloak_id = CAST(:uid AS uuid), username = :username, "
                "role = 'SYSTEM_ADMIN', assigned_region_id = NULL, is_active = TRUE, "
                "updated_at = now() "
                "WHERE username = :username OR keycloak_id = CAST(:uid AS uuid)"
            ),
            params,
        )
        conn.execute(
            text(
                "INSERT INTO wims.users (user_id, keycloak_id, username, role, assigned_region_id, "
                "is_active) SELECT CAST(:uid AS uuid), CAST(:uid AS uuid), :username, "
                "'SYSTEM_ADMIN', NULL, TRUE WHERE NOT EXISTS (SELECT 1 FROM wims.users "
                "WHERE username = :username OR keycloak_id = CAST(:uid AS uuid))"
            ),
            params,
        )

    print(f"\nBootstrap admin ready: {username} ({uid})")
    print("First login forces a password change and OTP enrolment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
