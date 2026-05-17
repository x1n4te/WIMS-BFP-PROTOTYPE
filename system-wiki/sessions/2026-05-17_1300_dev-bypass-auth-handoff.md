# Handoff — WIMS-BFP Dev Bypass Auth Endpoint

**Date:** 2026-05-17
**Session:** x1n4te / xynate
**Branch:** `dev/dev-bypass-auth`
**Status:** Implemented and verified working

---

## What Was Built

`POST /api/dev-login` — a Keycloak direct grant bypass endpoint that eliminates the OTP wall for dogfood QA sessions.

**Files created/modified:**

| File | Change |
|---|---|
| `src/backend/api/routes/auth.py` | **NEW** — dev bypass endpoint |
| `src/backend/main.py` | Added auth router import + `include_router` at `/api` |
| `src/keycloak/bfp-realm.json` | `wims-web.directAccessGrantsEnabled` set to `true` |
| `scripts/dev-keycloak-bypass.sh` | **NEW** — reusable enable/disable toggle script |
| `system-wiki/gaps/security-gap-register.md` | **NEW** — DEV-BYPASS-001 CRITICAL entry |
| `system-wiki/log.md` | Session summary appended |

---

## Key Implementation Details

### How the endpoint works

1. `POST /api/dev-login` accepts `{ role, username, password }`
2. Calls Keycloak token endpoint with `grant_type=password` + `client_id=wims-web`
3. Returns `{ access_token, refresh_token }`
4. Caller (dogfood QA) injects `access_token` as browser cookie via `browser_console`

**No JWT validation inside the endpoint** — the token is passed straight through. The token is validated downstream by `auth.authenticator.validate_token()` on every protected request.

### Critical discovery: audience mismatch

Keycloak issues tokens with `aud=wims-web` when `client_id=wims-web` is used in the direct grant call. The backend's `auth.py` validates against `audience=wims-web` (via `KEYCLOAK_AUDIENCE` env var). This match is required for `validate_token()` to pass.

**Previous incorrect approach:** Using `client_id=bfp-client` in the direct grant → Keycloak issued tokens with `aud=bfp-client` → `validate_token()` failed with "Invalid audience" → every protected endpoint returned 401.

**Fix:** Use `client_id=auth.CLIENT_ID` (which is `wims-web` from the `KEYCLOAK_CLIENT_ID` env var) in the direct grant. This produces tokens with `aud=wims-web`, matching what `validate_token()` expects.

### wims-web directAccessGrantsEnabled

The `bfp-realm.json` had `wims-web.directAccessGrantsEnabled: false`. A DB fix was required:
```sql
UPDATE client SET direct_access_grants_enabled = TRUE WHERE client_id = 'wims-web';
```

This is now permanently set in `bfp-realm.json` (line 873). However, Keycloak's `--import-realm` uses `IGNORE_EXISTING` strategy — once the realm exists in Keycloak, the JSON is NOT re-imported on restart.

**Consequence for fresh environments:** On a fresh Keycloak import, `wims-web` already has `directAccessGrantsEnabled=true` (from the updated JSON). On existing environments that already imported the realm, the DB state may differ from the JSON. Use `scripts/dev-keycloak-bypass.sh enable` to apply it.

---

## Toggle Script

```bash
# From repo root
./scripts/dev-keycloak-bypass.sh enable   # Enable wims-web direct grant + restart Keycloak
./scripts/dev-keycloak-bypass.sh disable  # Disable + restart
./scripts/dev-keycloak-bypass.sh status    # Show current state
```

The script modifies `keycloak.client.direct_access_grants_enabled` directly via psql.

---

## Verified Working

```python
# All confirmed via backend container python3:
POST /api/dev-login → 200, access_token + refresh_token
Token validates via auth.authenticator.validate_token() → sub, roles, aud OK
GET /api/user/me with cookie → 200, correct user data
GET /api/ref/regions with cookie → 403 "User not found in WIMS" (separate route issue, not the bypass)
```

---

## Dogfood QA Integration (for next session)

In dogfood Phase 0 — Authenticate:

```python
import requests
resp = requests.post("http://localhost:8000/api/dev-login", json={
    "role": "REGIONAL_ENCODER",  # or NATIONAL_VALIDATOR, NATIONAL_ANALYST, SYSTEM_ADMIN
    "username": "qa_auto",
    "password": "QaAuto2026!Aa"
})
token = resp.json()["access_token"]
# Inject into browser
browser_console(expression=f"document.cookie = 'access_token={token}; path=/'")
```

---

## Security Gap — DEV-BYPASS-001 CRITICAL

**File:** `system-wiki/gaps/security-gap-register.md`

- **Severity:** CRITICAL
- **Classification:** Intentional dev-only backdoor — NEVER SHIP TO PROD
- **Blast radius:** Full role impersonation for all 4 WIMS roles (REGIONAL_ENCODER, NATIONAL_VALIDATOR, NATIONAL_ANALYST, SYSTEM_ADMIN)
- **Removal criteria:** Delete `auth.py`, remove router from `main.py`, close the gap entry — branch never merged to main

---

## Follow-up

- `bfp-realm.json` updated — `wims-web.directAccessGrantsEnabled: true` — permanent
- `scripts/dev-keycloak-bypass.sh` — reusable, works for both fresh and existing Keycloak setups
- `qa_auto` account credentials: `qa_auto` / `QaAuto2026!Aa`
- Branch: `dev/dev-bypass-auth` — **do not merge to main/master**

---

## Persist to Wiki?

YES — append to `system-wiki/log.md` noting: branch created, endpoint implemented, script created, security gap filed, Keycloak DB fix applied, `bfp-realm.json` updated.