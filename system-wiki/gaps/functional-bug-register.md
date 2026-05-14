---
title: Functional Bug Register
created: 2026-05-14
updated: 2026-05-14
type: bug
tags: [wims-bfp, bug, functional, m12, needs-fix]
sources: []
status: open
---

# Functional Bug Register

Functional bugs reported by teammates during evaluation (2026-05-14). These are broken behaviors, not UI/UX improvement suggestions. All map to M12 User Management unless noted.

---

## M12 User Management Bugs

| # | Bug | Detail | Reported By | Status |
|---|---|---|---|---|
| F-01 | System Audit record_id shows "-" on create user | Admin system audit log shows `"-"` for `record_id` when the action is create user, instead of the actual newly created user ID. Indicates the audit logger is not capturing the returned ID from the user creation flow. | Teammate | Needs investigation |
| F-02 | First login allows empty First Name, Last Name, device name | Users can complete login without providing First Name, Last Name, and device name on first login. Keycloak user profile required-attribute validation is not being enforced on the frontend or is being bypassed. | Teammate | Needs fix |
| F-03 | No username change screen on first login | Admin expects new users to change their username on first login (e.g., from a temporary/department default to their real username). No UI screen or prompt exists for this — the incorrect username persists indefinitely. | Teammate | Needs implementation |
| F-04 | Session lifespan too short / aggressive logout | Users are logged out too quickly during normal workflow. Likely Keycloak token timeout (`access_token_lifespan` or `sso_session_idle_timeout`) set too aggressively in the realm or client config. | Teammate | Needs config review |
| F-05 | No account recovery if TOTP authenticator is deleted | If a user deletes their TOTP authenticator device ("nadelete-acc sa authenticator"), there is no fallback or admin-assisted recovery path — the account is permanently inaccessible. Requires admin Keycloak intervention or a backup codes flow. | Teammate | Needs recovery flow |

---

## Related
- [[gaps/ui-ux-gap-register]] — UI/UX improvement gaps (layout, metrics, TOTP UX, etc.)
- [[gaps/frs-codebase-gap-register]] — FRS/codebase verification targets
- [[concepts/frs-module-map]] — M12 User Management module routing
- [[security/security-baseline]] — auth and MFA baseline
