# Changelog

All notable changes to the WIMS-BFP project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- `.gitignore` — added `src/suricata/logs/` to prevent runtime log tracking
- Removed 19 tracked `__pycache__/*.pyc` files from git index (`src/backend/api/`, `src/backend/models/`)
- Removed tracked `src/suricata/logs/eve.json` (5.3 MB runtime log) from git index

### Added
- `CHANGELOG.md` — project changelog
- `docs/ARCHITECTURE.md` — system architecture overview
- `docs/API_AND_FUNCTIONS.md` — API and function reference
- `README.md` — root project README with quick start guide
- `.cursor/prompts/pre-push-audit-and-docs.prompt.md` — pre-push audit prompt

## [0.1.0] — 2026-03-14

### Added
- **Infrastructure:** Full Docker Compose orchestration with PostgreSQL/PostGIS, Redis, Keycloak, Ollama, Nginx gateway, Suricata IDS, Celery worker (`00657fe`, `13104b3`)
- **Authentication:** Complete OIDC PKCE flow via Keycloak; purged all legacy Supabase auth references; secured route contexts with role-based access (`e9d9a8a`)
- **Backend API:**
  - `POST /api/auth/callback` — Keycloak PKCE token exchange with user upsert
  - `GET /api/user/me` — JWT-protected user profile with JIT provisioning
  - `POST /api/incidents` — geospatial fire incident creation
  - `POST /api/civilian/reports` — public emergency report submission (no auth)
  - `GET /api/triage/pending` — pending citizen report queue
  - `POST /api/triage/{report_id}/promote` — promote citizen report to official incident
  - `GET/PATCH /api/admin/users` — user management (SYSTEM_ADMIN)
  - `GET/PATCH/POST /api/admin/security-logs` — threat log management with AI analysis
  - `GET /api/admin/audit-logs` — paginated audit trail
  - Rate-limiting middleware on `POST /api/auth/login` (Redis sliding window)
- **Supabase Edge Functions:** `analytics-summary`, `commit-incident`, `conflict-detection`, `security-event-action`, `upload-bundle`
- **Frontend pages:** Dashboard, incidents list/create/import/triage, incident detail with conflict detection, public report form, admin system hub, operations center (`/home`)
- **Database schema:** `wims` schema with PostGIS geography columns, soft-delete support, chain-of-custody audit trails, geographic reference tables (regions/provinces/cities/barangays)
- **Celery beat task:** Suricata EVE log ingestion every 10 seconds
- **Tests:** Adversarial integration suite for schema validation, infrastructure config tests (`9855eda`–`613e179`)

### Fixed
- Dark mode contrast classes on Threat Telemetry View modal in admin panel (`b8b33a0`)

### Security
- `.gitignore` rules for `.env`, `*.pem`, `*.key`, credential files (`1916a9b`)
- Untracked ignored files, caches, and runtime logs (`2817965`)
