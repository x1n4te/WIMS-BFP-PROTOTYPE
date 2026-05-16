---
title: Security Baseline
created: 2026-05-14
updated: 2026-05-15
type: security
tags: [wims-bfp, security, auth, rbac, rls, audit-log, ids, xai, privacy, fail-closed]
sources: [raw/frs/frs-auth.md, raw/frs/frs-complianceanddataprivacy.md, raw/frs/frs-intrusiondetectionandnetworkingmonitoring.md, raw/frs/frs-threatdetectionwithexplainableai.md, raw/codebase/codebase-snapshot-2026-05-14.md]
status: draft
---

# Security Baseline

## Auth and RBAC
FRS Module 1 defines Keycloak-backed authentication, MFA for privileged roles, session timeout, password policy, and role-based access control. Relevant implementation surfaces: `admin.py`, `sessions.py`, `user.py`, frontend auth API routes, and Keycloak config.

Development Keycloak realm config in `src/keycloak/bfp-realm.json` enables the built-in `reset credentials` flow, `resetPasswordAllowed`, and MailHog SMTP defaults (`mailhog:1025`, `noreply@wims-bfp.local`) for local forgot-password testing. `src/docker-compose.yml` includes a MailHog service exposing SMTP on `1025` and the web/API UI on `8025`.

## Fail-Closed Rule
Any missing authentication context defaults to deny. Public unauthenticated behavior is limited to the explicit public DMZ submission route in `public_dmz.py`; all adjacent APIs should require valid role context.

## RLS and Data Privacy
FRS Module 10 requires minimization, purpose limitation, rectification/erasure handling, breach notification, DPIA, and RoPA. Database enforcement must be verified in `src/postgres-init/09_rls_helpers.sql`, `10_rls_policies.sql`, and route dependencies.

## Audit and Immutability
FRS Module 4 requires SHA-256 data hashes, append-only audit logs, and immutable commit records. Verification/correction workflow remains a high-risk area; see [[gaps/frs-codebase-gap-register]].

## IDS/XAI
FRS Modules 7 and 8 define Suricata network monitoring and Qwen2.5-3B explainability. Relevant code/config: `src/suricata/`, admin security-log routes, and AI service paths.

## Related
- [[database/schema-overview]]
- [[backend/api-route-map]]
