---
title: System Overview
created: 2026-05-14
updated: 2026-05-14
type: architecture
tags: [wims-bfp, codebase, backend, frontend, database, docker]
sources: [raw/codebase/codebase-snapshot-2026-05-14.md, AGENTS.md]
status: draft
---

# System Overview

WIMS-BFP is a Dockerized full-stack prototype centered on fire incident reporting, validation, analytics, security monitoring, and administrative workflows.

## Major Layers
- Frontend: Next.js App Router in `src/frontend/src/app`, mapped in [[frontend/route-map]].
- Backend: FastAPI route modules in `src/backend/api/routes`, mapped in [[backend/api-route-map]].
- Database: PostgreSQL/PostGIS bootstrap and migrations in `src/postgres-init`, mapped in [[database/schema-overview]].
- Identity: Keycloak realm/config files in `src/keycloak`; enforced through backend dependencies and frontend OIDC flows; see [[security/security-baseline]].
- Edge/infra: Docker Compose, Nginx reverse proxy, Redis/Celery workers, Suricata logs/rules.

## Current Completion Heuristic
The user estimates the current codebase is roughly 60 percent of agreed FRS feature scope. Treat this as a planning heuristic, not a verified metric. Verification belongs in [[gaps/frs-codebase-gap-register]].

## Architecture Gate
Prefer direct subsystem edits over broad abstraction. Do not split `regional.py` opportunistically; current project memory says the large route file is intentionally not being refactored during active feature work.

## Related
- [[concepts/frs-module-map]]
- [[operations/agent-routing-guide]]
