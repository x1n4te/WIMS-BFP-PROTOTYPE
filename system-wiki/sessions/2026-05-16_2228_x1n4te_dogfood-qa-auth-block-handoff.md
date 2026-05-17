# Handoff — WIMS-BFP Dogfood QA (Auth Block)

**Date:** 2026-05-16
**Session:** x1n4te / xynate
**Last status:** Browser CDP dead, auth OTP wall partially fixed, test account `qa_auto` created

---

## What Happened

The browser CDP connection died mid-session (`Auto-launch failed: CDP WebSocket connect failed: HTTP error: 404 Not Found`). Before dying, we were working through the Keycloak OTP authentication wall for dogfood QA.

### Auth Wall — Root Cause

The `Browser - Conditional OTP` authentication flow had `auth-otp-form` at **priority 40 as REQUIRED** — meaning ALL users hitting it regardless of role. The fix applied to the DB directly:

1. `auth-otp-form` execution `requirement` changed from `0` (REQUIRED) to `2` (ALTERNATIVE)
2. Added a new `conditional-user-role` execution at **priority 35** with `condUserRole=REGIONAL_ENCODER` to bypass OTP for encoder role
3. Previous DB fix: `authenticator_config_entry` values for existing conditionals updated from `system_administrator` → `SYSTEM_ADMIN`, `national_validator` → `NATIONAL_VALIDATOR`

### Auth Flow Architecture (Browser - Conditional OTP)

| Priority | Execution | Type | Config |
|----------|-----------|------|--------|
| 10 | `conditional-user-configured` | ALTERNATIVE | — |
| 20 | `conditional-user-role` | ALTERNATIVE | `condUserRole=SYSTEM_ADMIN` |
| 30 | `conditional-user-role` | ALTERNATIVE | `condUserRole=NATIONAL_VALIDATOR` |
| 35 | `conditional-user-role` | ALTERNATIVE | `condUserRole=REGIONAL_ENCODER` ← NEW |
| 40 | `auth-otp-form` | ALTERNATIVE | — |

### Test Account Created

- **Username:** `qa_auto`
- **Password:** `QaAuto2026!Aa` (complies with BFP 12+ char policy)
- **Keycloak ID:** `6c0f9320-2319-4f25-8cdd-33b8ad9878a7`
- **Roles:** `REGIONAL_ENCODER`
- **Profile:** `firstName`, `lastName`, `emailVerified: true`, `requiredActions: []`
- **OTP status:** `totp: false` (no TOTP enrollment)

### Verified Working

- `qa_auto` can generate access tokens via direct grant (`client_id=bfp-client`)
- Password policy: 12+ chars, 1 upper, 1 lower, 1 digit, 1 special char
- BFP realm ID: `0d7644e4-1107-4da2-83f4-ca7ac87ce39b`

### Other Test Accounts (Broken)

- `encoder_test`, `admin_test`, `analyst1_test` — all return `invalid_grant: Account is not fully set up` via direct grant. This is Keycloak's error for incomplete user profile. Do NOT use these.

---

## Still Needed

1. **Re-establish browser CDP** — the browser session is dead. Needs manual relaunch (`/browser connect` or equivalent)
2. **Test `qa_auto` login** at `http://localhost` — verify OTP wall is bypassed with the DB fixes in place
3. **If OTP still fires:** add more `conditional-user-role` executions for other roles (ANALYST, VALIDATOR), or set `auth-otp-form` execution to DISABLED (requirement=3)
4. **Capture session cookies** after successful login
5. **Full dogfood walkthrough:** Public landing → Login → Encoder dashboard → Incident submission → Validator dashboard

---

## Key Files

| File | Purpose |
|------|---------|
| `src/keycloak/bfp-realm.json` | Realm config — changes NOT yet synced to running Keycloak |
| `src/frontend/src/lib/oidc.ts` | OIDC config, authority `/auth/realms/bfp` |
| `src/frontend/src/app/callback/page.tsx` | Post-auth, calls `/api/auth/sync` |
| `src/frontend/src/app/api/auth/sync/route.ts` | Sets httpOnly cookies (5 min / 8 hrs) |
| `src/backend/services/keycloak_admin.py` | Keycloak admin SDK pattern |
| `system-wiki/gaps/frs-codebase-gap-register.md` | Known gaps |

---

## Suggested Next Session

**Next session goal:** Resume dogfood QA — reconnect browser, test `qa_auto` login, proceed to Phase 1 walkthrough.

**Skills to load:** `qa/dogfood` (primary), `hermes-agent` (for browser CDP setup if needed)

**Credentials:**
- Keycloak master: `[REDACTED]` / `[REDACTED]`
- Test account: `qa_auto` / `QaAuto2026!Aa`

---

## Persist to Wiki?

YES — append session summary to `system-wiki/log.md` and update `system-wiki/gaps/frs-codebase-gap-register.md` if any new gaps were found during auth debugging.