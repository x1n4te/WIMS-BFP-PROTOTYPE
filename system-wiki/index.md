# WIMS-BFP System Wiki Index

Last updated: 2026-05-15
Total synthesis pages: 13
Purpose: project-local knowledgebase for agents routing themselves to relevant WIMS-BFP context.

## Start Here
- [[mocs/system-map]] — primary map of content and routing entry point.
- [[operations/agent-routing-guide]] — which page an agent should read before touching each subsystem.

## Architecture
- [[architecture/system-overview]] — Dockerized full-stack architecture, runtime services, and evidence sources.
- [[architecture/context-map]] — source-of-truth hierarchy and how FRS, code, and this wiki relate.

## Concepts
- [[concepts/frs-module-map]] — 15-module FRS map with current source availability and code anchors.

## Backend
- [[backend/api-route-map]] — FastAPI route files, endpoints, and likely module ownership.

## Frontend
- [[frontend/route-map]] — Next.js App Router pages and UI surface mapping.

## Database
- [[database/schema-overview]] — PostgreSQL/PostGIS tables and migration source files.

## Security
- [[security/security-baseline]] — auth, RBAC, RLS, audit, IDS/XAI, and fail-closed notes.

## Gaps
- [[gaps/frs-codebase-gap-register]] — FRS/codebase verification targets (hashing, RLS, notifications, offline-first, M9).
- [[gaps/ui-ux-gap-register]] — UI/UX improvement gaps (login layout, admin hub layout, TOTP UX, etc.).
- [[gaps/functional-bug-register]] — functional/auth bugs (M12: audit record_id, first-login validation, username change, session timeout, MFA lockout).

## UI/UX Evaluations
- [[ui-ux/evaluation-loginpage-keycloaksso]] — login misalignment, hero icon loss, TOTP digit-separation.
- [[ui-ux/evaluation-system-admin-hub]] — linear layout, missing M9 metrics, no pagination/filters, region selector, announcement feature.
- [[ui-ux/evaluation-national-analyst]] — heatmap aspect ratio, missing incident container, filter coverage, export preview, missing analytics views (top municipalities, response time); cross-referenced with FRS M5 and GitHub issues #84–#89.

## Raw Source Captures
- `raw/frs/` — user-supplied FRS module files (11 now populated; 4 were empty and restored).
- `raw/ui-ux/` — user desk-check evaluations of login page and system admin hub.
- `raw/codebase/codebase-snapshot-2026-05-14.md` — generated repository snapshot used for initialization.
