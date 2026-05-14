---
title: Login Page + Keycloak SSO — UI/UX Evaluation
created: 2026-05-14
updated: 2026-05-14
type: ui-ux
tags: [wims-bfp, ui-ux, auth, login, keycloak, hci]
sources: [raw/ui-ux/evaluation-loginpage+keycloaksso.md, raw/frs/frs-auth.md]
status: needs-review
---

# Login Page + Keycloak SSO — UI/UX Evaluation

Desk-check findings from user evaluation of the login page and Keycloak SSO flow.

## UX Issues Identified

### 1. Sign-In Container Alignment (Keycloak SSO)
The Keycloak SSO sign-in container is correctly centered. The native WIMS sign-in container is offset too far from the side edge, creating asymmetry between the two auth surfaces. The Keycloak container placement should be the reference for alignment consistency.

### 2. Hero Line Icon Loss on Keycloak Redirect
The hero line "Secured — Monitored — Explainable" includes a checkmark icon that disappears when the flow redirects to the Keycloak-hosted MFA screen. This breaks the visual continuity of the trust/brand signal. Restore the hero branding elements on the Keycloak MFA page, or ensure the container header retains visual identity during OIDC redirect.

### 3. MFA/TOTP Input — Digit-Separated Box UX
The current TOTP input treats the 6-digit code as a single undifferentiated field. The authenticator app produces a grouped display (e.g., `640 597`). The input should match this mental model:

- 6 individual boxes: `[0][0][0][0][0][0]` or grouped as `[00][00][00]` (3+3)
- Auto-advance on digit entry (cursor moves right)
- Backspace twice (or backspace on a non-first box) returns focus to previous box
- No submission until all 6 digits entered
- FRS anchor: M1.a.ii — TOTP via authenticator app with option to remember trusted device for 7 days

## FRS Module Alignment
- [[raw/frs/frs-auth]] Module 1.a.ii: MFA via TOTP required for System Administrators and National Validators

## Related
- [[security/security-baseline]]
- [[raw/ui-ux/evaluation-loginpage+keycloaksso]] (raw source)