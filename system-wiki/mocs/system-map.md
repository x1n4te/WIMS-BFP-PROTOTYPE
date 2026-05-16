---
title: System Map
created: 2026-05-14
updated: 2026-05-14
type: moc
tags: [wims-bfp, system-wiki, agent-routing, implementation-map]
sources: [SCHEMA.md, raw/codebase/codebase-snapshot-2026-05-14.md]
status: draft
---

# System Map

This is the first page agents should read after `SCHEMA.md` and `index.md`.

## Source-of-Truth Flow
`raw/frs/` -> [[concepts/frs-module-map]] -> implementation maps -> [[gaps/frs-codebase-gap-register]]

Implementation evidence flows from live files under `src/` into:
- [[backend/api-route-map]] for FastAPI route ownership.
- [[frontend/route-map]] for Next.js UI surfaces.
- [[database/schema-overview]] for schema/RLS/analytics tables.
- [[security/security-baseline]] for auth, RBAC, RLS, audit, IDS, and privacy posture.

## Runtime Layers
1. Browser/Next.js frontend: see [[frontend/route-map]].
2. FastAPI backend: see [[backend/api-route-map]].
3. PostgreSQL/PostGIS + init SQL: see [[database/schema-overview]].
4. Keycloak/OIDC + role enforcement: see [[security/security-baseline]].
5. Redis/Celery/SSE/notifications: route and implementation details are partially visible in [[backend/api-route-map]] and must be deep-scanned before edits.
6. Suricata + XAI security monitoring: see [[security/security-baseline]].

## Agent Routing
Use [[operations/agent-routing-guide]] before assigning work. Minimum context principle: route agents only the pages and source files needed for their subsystem.
