# Repository Guidelines

## Project Structure & Module Organization

This repository is a Dockerized WIMS-BFP full-stack prototype. Primary implementation lives in `src/`: `src/backend/` contains the FastAPI API, Celery tasks, models, schemas, and pytest tests; `src/frontend/` contains the Next.js App Router application, React components, client libraries, public assets, and Vitest tests. Database bootstrap SQL is in `src/postgres-init/`. Keycloak files are in `src/keycloak/`, Nginx config is in `src/nginx/`, and Suricata rules/log mounts are in `src/suricata/`. Project notes live in `docs/`; seed and utility scripts live in `scripts/`.

## System Wiki & Agent Context Routing

A project-local system knowledgebase lives in `system-wiki/`. This is the authoritative agent-routing wiki for the current implementation state of this repository, separate from any thesis-level wiki or external research vault.

Before making non-trivial changes, agents should read:

1. `AGENTS.md`
2. `system-wiki/SCHEMA.md`
3. `system-wiki/index.md`
4. `system-wiki/mocs/system-map.md`
5. The relevant subsystem page listed in `system-wiki/operations/agent-routing-guide.md`

Key system-wiki pages:

- `system-wiki/mocs/system-map.md`: high-level entry point and source-of-truth flow.
- `system-wiki/operations/agent-routing-guide.md`: subsystem-specific context packs for auth, incident workflow, validation, immutable records, analytics, public DMZ, and reference data work.
- `system-wiki/concepts/frs-module-map.md`: 15-module FRS-to-code routing map.
- `system-wiki/backend/api-route-map.md`: FastAPI route ownership snapshot.
- `system-wiki/frontend/route-map.md`: Next.js route surface map.
- `system-wiki/database/schema-overview.md`: PostgreSQL/PostGIS table and migration map.
- `system-wiki/security/security-baseline.md`: auth/RBAC/RLS/audit/IDS/XAI security baseline.
- `system-wiki/gaps/frs-codebase-gap-register.md`: known FRS/codebase gaps and verification targets.

Raw FRS files are copied under `system-wiki/raw/frs/` and must be treated as source material. Do not edit raw wiki sources directly unless replacing them with a newer authoritative FRS batch. When desk checks reveal the current true system state, update the relevant synthesis page plus `system-wiki/gaps/frs-codebase-gap-register.md` and append the change to `system-wiki/log.md`.

## Build, Test, and Development Commands

- `cd src && docker compose down -v && docker compose build --no-cache && docker compose up -d`: **clean-slate init** — destroys containers and volumes, fresh image build, cold start. First boot runs all 34 SQL bootstrap files in `postgres-init/` and imports Keycloak realm.
- `cd src && docker compose down`: stop the stack without deleting volumes (preserves DB data).
- `cd src && docker compose up --build -d`: restart with rebuild (preserves data volumes).
- `cd src/backend && pytest -v`: run backend unit and integration tests from `src/backend/tests`.
- `cd src/frontend && npm run dev`: start the Next.js dev server.
- `cd src/frontend && npm run build`: create a production frontend build.
- `cd src/frontend && npm run lint`: run ESLint.
- `cd src/frontend && npx vitest run`: run frontend tests.

Install frontend dependencies with `npm install` in `src/frontend/`. For non-Docker backend work, install `src/backend/requirements.txt` in a Python 3.10+ virtual environment.

## Coding Style & Naming Conventions

Use Python 3.10+ style in the backend: 4-space indentation, typed FastAPI route signatures where practical, `snake_case` for functions/modules, and explicit Pydantic schemas in `schemas/`. Keep routes grouped by domain under `src/backend/api/routes/`.

Frontend code is TypeScript/React. Use `PascalCase` for components, `camelCase` for functions and variables, and colocate tests beside code. Follow existing ESLint and Next.js conventions; avoid broad formatting churn.

## Testing Guidelines

Backend pytest discovery is configured in `src/backend/pytest.ini` with `testpaths = tests`. Name tests `test_*.py`; place integration-heavy cases under `src/backend/tests/integration/`. Frontend tests use Vitest, React Testing Library, and jsdom; name files `*.test.ts` or `*.test.tsx`. Run relevant tests before opening a PR.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style subjects, often with issue references, such as `feat(#46): ...`, `fix(auth): ...`, and `style: ...`. Keep subjects imperative and scoped when useful.

Pull requests should include a short problem/solution summary, linked issues, test results, and screenshots for visible UI changes. Call out schema, auth, environment, or data-volume impacts explicitly. Never commit real secrets; Docker Compose values are development defaults only.
