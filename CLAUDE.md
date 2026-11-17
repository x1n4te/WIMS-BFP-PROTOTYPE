# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build, Test, and Development Commands

```bash
# Full stack — clean-slate init (wipe volumes, fresh build, cold start)
cd src && docker compose down -v
cd src && docker compose build --no-cache
cd src && docker compose up -d

# Full stack — restart (preserves data volumes)
cd src && docker compose down
cd src && docker compose up --build -d

# Backend
cd src/backend && pytest -v
cd src/backend && ruff check .

# Frontend
cd src/frontend && npm run dev
cd src/frontend && npx vitest run
cd src/frontend && npm run lint

# Local CI simulation
make ci-local

# Format
make format
```

> **Clean-slate init:** First boot runs all 74 SQL bootstrap files in `postgres-init/` and imports the Keycloak realm. Subsequent boots skip both. Use `down -v` when you want a fully fresh database (schema + seed data + Keycloak users).

## Architecture

WIMS-BFP is a Dockerized full-stack incident management system for the Philippine Bureau of Fire Protection.

```
src/
├── backend/                # FastAPI + Celery (Python 3.10+)
│   ├── api/routes/         # incidents, analytics, regional, admin (civilian/triage/public routers kept but unmounted)
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # AI/XAI, analytics, duplicate detection
│   ├── tasks/              # Celery tasks (Suricata, exports, drafts)
│   └── utils/              # crypto (AES-256-GCM), session revocation, audit
├── frontend/               # Next.js 16 (App Router), React 19, TypeScript, TailwindCSS 4
├── postgres-init/          # 75 SQL bootstrap files (ordered, run at first boot)
├── keycloak/               # Realm import JSON (bfp-realm.json)
├── openbao/                # OpenBao init/bootstrap for KMS
├── suricata/               # Suricata IDS rules/log mounts
├── nginx/                  # Nginx edge gateway config
├── docker-compose.yml      # services: postgres, redis, mailhog, keycloak,
│                           # keycloak-bootstrap, openbao, openbao-bootstrap,
│                           # backend, celery-worker, frontend, nginx-gateway
│                           # (turnover Phase 3: no suricata, ollama or osrm)
└── docker-compose.override.yml / docker-compose.ci.yml / docker-compose.prod.yml
```

## Key Patterns

### Auth and RLS

Keycloak JWT tokens carry WIMS roles. Backend auth (`auth.py`) extracts roles from `realm_access.roles` or `resource_access.<client>.roles` using the precedence order: `CIVILIAN_REPORTER` → `REGIONAL_ENCODER` → `NATIONAL_VALIDATOR` → `NATIONAL_ANALYST` → `SYSTEM_ADMIN`.

**Row Level Security** uses a PostgreSQL GUC `wims.current_user_id` set via `SET LOCAL wims.current_user_id` at the start of each transaction. The `database.py` `set_rls_context()` function applies this. All `wims.*` tables have RLS policies bound to this GUC.

Dependency order matters: `get_current_wims_user` must be listed **before** `get_db_with_rls` in route signatures so `request.state.wims_user` is populated before RLS context is set.

**Session revocation** is implemented in `utils/session.py` via Redis. When a user is deactivated, their `keycloak_id` + revocation timestamp is stored in Redis. Every request through `auth.py` checks this blacklist to instantly reject revoked JWTs.

### PII Encryption

PII fields (`caller_name`, `caller_number`, `owner_name`, `occupant_name`) in `wims.incident_sensitive_details` are encrypted at rest with AES-256-GCM via `utils/crypto.py`. Plaintext columns are always `NULL` for new writes. The key comes from `WIMS_MASTER_KEY` env var. Decryption failures log a `CRITICAL` event and fall back to legacy plaintext columns (fail-closed).

### Incident Pipeline

**Turnover build (Phase 3):** the civilian/public intake (`/api/civilian`, `/api/v1/public`, `/api/triage`, `/api/operations`, community/information, perimeters) is **not mounted**; the source modules are kept. Staff intake only:

1. Encoders create incidents or import AFOR workbooks (`POST /api/regional/afor/import` then `/commit`, structural; SYSTEM_ADMIN may import too, with a chosen region). Imports are DRAFT.
2. `PATCH /api/regional/incidents/{id}/submit` -> PENDING; NATIONAL_VALIDATOR approves/rejects (`/verification`).
3. Analysts read via `/api/analytics/*` (exports run in Celery).

### Keycloak Configuration

Keycloak uses `--import-realm` with `IGNORE_EXISTING` strategy. Once the realm exists, the JSON is NOT re-imported. The only realm file is `src/keycloak/import/bfp-realm.json` (the former root `src/keycloak/bfp-realm.json` was removed). The realm ships with **no users**: create the first SYSTEM_ADMIN with `scripts/bootstrap-admin.sh` (env `BOOTSTRAP_ADMIN_USERNAME`/`_EMAIL`/`_PASSWORD`; forces password change + OTP enrolment on first login), then create everyone else through the admin UI. For local development only, `scripts/seed-dev-users.sh` creates the dev accounts. OTP is required for `SYSTEM_ADMIN` and `NATIONAL_VALIDATOR` only (built-in OTP form, conditional on realm role).

Admin roles and credentials (turnover Phase 2): `SYSTEM_ADMIN` may also import AFOR files (region chosen per import) and submit its own drafts, but never approves (approval routes keep `get_national_validator`). When Keycloak email is unavailable an admin can type a temporary password (`POST /api/admin/users/{keycloak_id}/temporary-password`; set as temporary, audit row has no password). The daily Celery task `tasks.password_expiry.enforce_password_expiry` adds UPDATE_PASSWORD for `SYSTEM_ADMIN`/`NATIONAL_VALIDATOR` users whose password is older than 90 days. Backend and celery-worker need `KEYCLOAK_ADMIN_USER` (or `KEYCLOAK_ADMIN`) and `KEYCLOAK_ADMIN_PASSWORD`; there is no admin/admin fallback.

Two issuer URLs exist: backend fetches JWKS from `keycloak:8080` (Docker internal) but validates tokens against `localhost` (browser-visible, set via `KC_HOSTNAME=localhost`).

### Removed in the turnover build (Phase 3)

Suricata IDS ingestion, the HITL threat flow (`/api/admin/security-logs*`), Ollama/AI narratives, the IP/device blocklist admin routers, FCM push, Turnstile and OSRM routing are unmounted/unscheduled (beat has no Suricata, AI-queue, civilian, blocklist or community jobs) and their compose services are gone. Source files stay. Breaches are logged manually (`POST /api/admin/breach`), which writes a backing `security_threat_logs` row because `breach_notifications.threat_log_id` is NOT NULL. `tests/conftest.py` lists the skipped tests of unmounted features.

### Offline/PWA

The frontend supports offline-first operation for encoders, validators, analysts, and admin. Key modules:
- `src/frontend/src/lib/offlineStore.ts` — IndexedDB layer with stores for `offlineOps`, `cachedIncidents`, `analytics-cache`, per-user key isolation, and legacy `incident-queue` compat (DB_VERSION 4).
- `src/frontend/src/lib/syncEngine.ts` — Dispatches pending ops on connectivity restore; dual-path for both `offlineOps` (PR #271) and legacy `incident-queue` (PR #272).
- `src/frontend/src/lib/connectivity.ts` — Singleton monitor with exponential backoff recheck loop.
- `src/frontend/src/lib/api/offline*.ts` — Offline-aware read wrappers for analytics, regional, validator, and admin.
- Public manifest at `src/frontend/public/manifest.webmanifest`.

The offline/PWA architecture is expressed in the source modules themselves. Read `src/frontend/src/lib/offlineStore.ts`, `syncEngine.ts`, `connectivity.ts`, and the offline-aware API wrappers for the current state. See `docs/agents/gotchas.md` for known failure modes.

## Agent Routing

The code is the source of truth. Read the relevant source, tests, config, and scoped AGENTS.md before changing anything:

| Topic | Read first |
|---|---|
| Auth/RBAC/RLS | `src/backend/services/auth.py`, `src/backend/utils/database.py` (RLS context), `src/postgres-init/` (RLS policies) |
| Incident workflow | `src/backend/api/routes/`, related service in `src/backend/services/` |
| Analytics | `src/backend/services/analytics/`, `src/backend/api/routes/analytics/` |
| Database schema | `src/postgres-init/*.sql` (ordered bootstrap), `src/backend/alembic/versions/` (migrations) |
| Offline/PWA | `src/frontend/src/lib/offlineStore.ts`, `syncEngine.ts`, `connectivity.ts` |
| Infrastructure | `src/docker-compose*.yml`, `src/nginx/`, `src/AGENTS.md` |
| Security baseline | `src/AGENTS.md` (non-negotiable rules), `docs/agents/gotchas.md` |

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `x1n4te/WIMS-BFP-PROTOTYPE` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The canonical triage labels are `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain context

`AGENTS.md` and `CLAUDE.md` are the entry points. Read the relevant scoped AGENTS.md (`src/AGENTS.md`, `src/backend/AGENTS.md`, `src/frontend/AGENTS.md`) for deeper subsystem rules. The root AGENTS.md "Code as Source of Truth" section governs: if a written claim conflicts with the code, the code wins.

## Testing

Backend pytest discovery: `testpaths = tests` in `pytest.ini`. Integration tests under `src/backend/tests/integration/`. Frontend tests use Vitest + React Testing Library + jsdom. Run `make ci-local` before opening a PR.

## Key Environment Variables

| Variable | Service | Purpose |
|---|---|---|
| `DATABASE_URL` | backend, celery | PostgreSQL connection |
| `DATABASE_ADMIN_URL` | backend | Postgres superuser for DDL patches |
| `KEYCLOAK_REALM_URL` | backend | Keycloak JWKS endpoint (Docker internal) |
| `KEYCLOAK_ISSUER` | backend | JWT `iss` validation (browser-visible) |
| `WIMS_MASTER_KEY` | backend | AES-256-GCM encryption key for PII |
| `REDIS_URL` | backend, celery | Rate limiting + Celery broker + session blacklist |
| `OLLAMA_URL` | backend | Local LLM for XAI narratives |
| `NEXT_PUBLIC_API_URL` | frontend | Backend API base URL |
| `NEXT_PUBLIC_AUTH_API_URL` | frontend | Keycloak auth URL (required; build fails if unset) |
| `NEXT_PUBLIC_BASE_URL` | frontend | Public base URL (required; build fails if unset) |

> Frontend build requires `NEXT_PUBLIC_AUTH_API_URL` and `NEXT_PUBLIC_BASE_URL`. Safe dummy values: `NEXT_PUBLIC_AUTH_API_URL=http://localhost:8080/auth` `NEXT_PUBLIC_BASE_URL=http://localhost:3000`.
