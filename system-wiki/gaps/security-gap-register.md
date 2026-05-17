---
title: Security Gap Register
created: 2026-05-17
updated: 2026-05-17
type: security-gap
tags: [wims-bfp, security, gap, critical, auth-bypass]
sources: [src/backend/api/routes/auth.py, src/backend/main.py, src/keycloak/bfp-realm.json, scripts/dev-keycloak-bypass.sh]
status: open
---

# Security Gap Register

> CRITICAL: Intentional dev-only backdoors. NEVER SHIP TO PROD. Audit before any deployment.

---

## DEV-BYPASS-001 | CRITICAL | Keycloak Direct Grant Backdoor — `/api/dev-login`

| Field | Detail |
|---|---|
| **Severity** | CRITICAL |
| **Status** | Open — active on `dev/dev-bypass-auth` only |
| **Discovered** | 2026-05-17 |
| **Branch** | `dev/dev-bypass-auth` — **NEVER merge to main/master** |
| **Affected Files** | `src/backend/api/routes/auth.py` (new), `src/backend/main.py` (modified), `src/keycloak/bfp-realm.json` (modified), `scripts/dev-keycloak-bypass.sh` (new) |
| **FRS Module** | M1 (Auth/NAT), M12 (User Management) |
| **Toggle Script** | `scripts/dev-keycloak-bypass.sh enable\|disable\|status` |

### Description

`POST /api/dev-login` authenticates against Keycloak's Resource Owner Password Credentials Grant (direct grant) using `client_id=wims-web` and returns real signed JWTs for any of 4 WIMS roles. This is a QA/debug artifact with no production use case.

**Mechanism:**
1. Endpoint receives `{ role, username, password }`
2. Calls `POST /auth/realms/bfp/protocol/openid-connect/token` with `grant_type=password` + `client_id=wims-web`
3. Keycloak issues token with `aud=wims-web` (matching `KEYCLOAK_AUDIENCE` env var)
4. Backend `auth.authenticator.validate_token()` accepts the token on subsequent protected requests
5. Returns `{ access_token, refresh_token }` — caller injects as browser cookie

**Roles exposed:** REGIONAL_ENCODER, NATIONAL_VALIDATOR, NATIONAL_ANALYST, SYSTEM_ADMIN

### Blast Radius

Full role impersonation. An attacker with network access to the endpoint can obtain valid Keycloak JWTs for any of the 4 roles — bypassing all RBAC enforcement and RLS context (`wims.current_user_id` GUC).

| Exposed Role | Blast Radius |
|---|---|
| REGIONAL_ENCODER | Import AFOR data, view incidents in assigned region |
| NATIONAL_VALIDATOR | Promote/demote incidents, access triage queue |
| NATIONAL_ANALYST | Full analytics dashboard, export capabilities |
| SYSTEM_ADMIN | User management, session revocation, system config |

**PII risk:** Incident caller names/numbers encrypted with AES-256-GCM, but all incident data and audit logs accessible per role.

### PoC

```bash
# Successful token acquisition
curl -X POST http://localhost:8000/api/dev-login \
  -H "Content-Type: application/json" \
  -d '{"role":"SYSTEM_ADMIN","username":"qa_auto","password":"QaAuto2026!Aa"}'
# Returns: {"access_token": "eyJ...", "refresh_token": "eyJ..."}

# Token accepted by all protected endpoints
curl http://localhost:8000/api/user/me \
  -H "Cookie: access_token=<token>"
# Returns: 200 {"username":"qa_auto","role":"SYSTEM_ADMIN",...}
```

### Toggle Script

```bash
./scripts/dev-keycloak-bypass.sh enable   # Enable wims-web direct grant + restart Keycloak
./scripts/dev-keycloak-bypass.sh disable  # Disable + restart  
./scripts/dev-keycloak-bypass.sh status   # Current state
```

This script modifies `keycloak.client.direct_access_grants_enabled` via psql. Required because Keycloak's `--import-realm` uses `IGNORE_EXISTING` — once realm exists, JSON is not re-imported.

### Keycloak DB Dependency

The `wims-web` client in `bfp-realm.json` now has `directAccessGrantsEnabled: true` (line 873). On **fresh** Keycloak imports this is applied automatically. On **existing** Keycloak instances, run `scripts/dev-keycloak-bypass.sh enable` to apply the DB-level change.

### Removal Criteria

All of the following must be completed before closing this gap:

- [ ] Delete `src/backend/api/routes/auth.py`
- [ ] Remove `from api.routes.auth import router as auth_router` from `src/backend/main.py`
- [ ] Remove `app.include_router(auth_router, prefix="/api")` from `src/backend/main.py`
- [ ] Revert `src/keycloak/bfp-realm.json` — `wims-web.directAccessGrantsEnabled` back to `false` (line 873)
- [ ] Close this entry with "Removed" status and removal date
- [ ] Branch `dev/dev-bypass-auth` deleted or merged to a throwaway branch

### Related

- [[security/security-baseline]] — auth/RBAC/RLS baseline
- [[gaps/frs-codebase-gap-register]] — FRS/codebase gap tracker
- `src/backend/api/routes/auth.py`
- `src/backend/main.py`
- `scripts/dev-keycloak-bypass.sh`
- `system-wiki/sessions/2026-05-17_1300_dev-bypass-auth-handoff.md`