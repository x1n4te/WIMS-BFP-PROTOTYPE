---
title: Agent Routing Guide
created: 2026-05-14
updated: 2026-05-14
type: operations
tags: [wims-bfp, agent-routing, implementation-map]
sources: [SCHEMA.md, index.md]
status: draft
---

# Agent Routing Guide

## Default Context Pack
Every WIMS-BFP agent touching this repo should read:
1. `AGENTS.md`
2. `system-wiki/SCHEMA.md`
3. `system-wiki/index.md`
4. [[mocs/system-map]]

## Route by Task
- Auth/session/user admin: read [[security/security-baseline]], [[backend/api-route-map]], then `src/backend/api/routes/admin.py`, `sessions.py`, `user.py`, and frontend auth routes.
- Incident CRUD/offline/import: read [[concepts/frs-module-map]], [[backend/api-route-map]], [[frontend/route-map]], then `regional.py`, `incidents.py`, offline/sync frontend libs.
- Validation/triage/duplicates: read [[backend/api-route-map]], [[database/schema-overview]], then `triage.py`, `regional.py`, duplicate detection service, and validator UI pages.
- Immutable records/audit/corrections: read [[security/security-baseline]], [[database/schema-overview]], [[gaps/frs-codebase-gap-register]], then immutable SQL/tests and verification endpoints.
- Analytics/reporting: read [[frontend/route-map]], [[backend/api-route-map]], [[database/schema-overview]], then `analytics.py`, analytics SQL, analyst dashboard, report pages.
- Public anonymous submission: read [[security/security-baseline]] and [[gaps/frs-codebase-gap-register]], then `public_dmz.py`, `triage.py`, and public report UI pages.
- Reference data: read [[database/schema-overview]], then `ref.py` and `02_ref_geography.sql` plus later geography seed files.

## Delegation Rules
- Security-sensitive work gets explicit security review before merge.
- Do not mix opportunistic refactors with bug fixes.
- Do not route an agent the full repo if a subsystem context pack is enough.
- Do not treat this wiki as more authoritative than raw FRS or live code.
