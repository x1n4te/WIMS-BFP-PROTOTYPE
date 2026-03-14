# WIMS-BFP API & Function Reference

## Backend API Routes (FastAPI)

Source: `src/backend/main.py` and `src/backend/api/routes/`

### Authentication (`main.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | None | Stub endpoint; always returns 401. Rate-limited (5 req / 900s via Redis). |
| POST | `/api/auth/callback` | None | PKCE token exchange: accepts `code` + `code_verifier`, exchanges with Keycloak, upserts user in `wims.users`, returns `access_token` + `user_id`. |
| GET | `/api/user/me` | JWT | Returns merged JWT claims + `wims.users` profile. JIT-provisions user record if missing. |

### Incidents (`api/routes/incidents.py` — prefix `/api`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/incidents` | `get_current_wims_user` | Create a fire incident with geospatial intake (PostGIS POINT). |

### Civilian Reports (`api/routes/civilian.py` — prefix `/api/civilian`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/civilian/reports` | None (public) | Submit an emergency report. `trust_score` is always 0 for public submissions. |

### Triage (`api/routes/triage.py` — prefix `/api/triage`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/triage/pending` | ENCODER / VALIDATOR | List `citizen_reports` with status `PENDING`. |
| POST | `/api/triage/{report_id}/promote` | ENCODER / VALIDATOR | Promote a pending citizen report to an official fire incident. |

### Admin (`api/routes/admin.py` — prefix `/api/admin`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/admin/users` | SYSTEM_ADMIN | List all users with masked Keycloak IDs. |
| PATCH | `/api/admin/users/{user_id}` | SYSTEM_ADMIN | Update user role, `assigned_region_id`, or `is_active`. |
| GET | `/api/admin/security-logs` | SYSTEM_ADMIN | List security threat logs ordered by timestamp descending. |
| POST | `/api/admin/security-logs/{log_id}/analyze` | SYSTEM_ADMIN | Trigger AI analysis via Ollama; updates `xai_narrative` and `xai_confidence`. |
| PATCH | `/api/admin/security-logs/{log_id}` | SYSTEM_ADMIN | Update `admin_action_taken` and `resolved_at` on a threat log. |
| GET | `/api/admin/audit-logs` | SYSTEM_ADMIN | Paginated system audit trails (`limit`, `offset` params). |

### Auth Dependencies (`auth.py`)

| Dependency | Purpose |
|------------|---------|
| `get_current_user` | Extracts JWT from `access_token` cookie or `Authorization: Bearer` header; validates via Keycloak JWKS. |
| `get_current_wims_user` | Validates JWT and resolves the user record in `wims.users`; returns 403 if not found. |
| `get_system_admin` | Requires `role == 'SYSTEM_ADMIN'`; returns 403 otherwise. |

---

## Supabase Edge Functions

Source: `src/supabase/functions/`

| Function | Auth | Description |
|----------|------|-------------|
| **analytics-summary** | ANALYST / ADMIN / SYSTEM_ADMIN (+ NHQ ENCODER/VALIDATOR) | Returns incident analytics: counts by region, alarm level, and general category. Supports date range, region, province, and city filters. |
| **commit-incident** | VALIDATOR / ADMIN / SYSTEM_ADMIN | Changes incident status (VERIFY, REJECT, MERGE). Updates `fire_incidents`, inserts `incident_verification_history`, writes audit trail. Validators limited to their assigned region. |
| **conflict-detection** | VALIDATOR / ADMIN / SYSTEM_ADMIN | Finds potential duplicate incidents within a 2-hour window, same region/city, and similar barangay. Writes verification history notes for each match. |
| **security-event-action** | ADMIN / SYSTEM_ADMIN | Updates security threat logs with `admin_action_taken` and `reviewed_by`; writes audit entry to `system_audit_trails`. |
| **upload-bundle** | ENCODER | Bulk-uploads fire incidents from XLSX/CSV import. Creates `data_import_batches` record, inserts into `fire_incidents`, `incident_nonsensitive_details`, and `incident_sensitive_details`. Enforces region matching. |

Shared module: `_shared/cors.ts` — common CORS headers for all functions.

Tests: `src/supabase/functions/tests/` — unit tests for `analytics-summary`, `commit-incident`, `conflict-detection`.

---

## Celery Background Tasks

Source: `src/backend/tasks/`

| Task | Schedule | Description |
|------|----------|-------------|
| `tasks.suricata.ingest_suricata_eve` | Every 10 seconds (beat) | Reads Suricata EVE JSON log file, parses alert events, and inserts new entries into `wims.security_threat_logs`. |

---

## Frontend Pages

Source: `src/frontend/src/app/`

### Public Routes (no auth required)

| Path | Component | Purpose |
|------|-----------|---------|
| `/` | Landing | Renders the login page |
| `/login` | LoginPage | Keycloak OIDC login; redirects to `/dashboard` when authenticated |
| `/callback` | CallbackPage | OIDC callback; processes Keycloak tokens, syncs session via `/api/auth/sync` |
| `/report` | ReportPage | Public emergency report form with map picker and description field |

### Protected Routes (auth required)

| Path | Component | Required Role | Purpose |
|------|-----------|---------------|---------|
| `/dashboard` | DashboardPage | Any authenticated | BFP incident dashboard: analytics cards, date/region/province/city filters. SYSTEM_ADMIN auto-redirects to `/admin/system`. |
| `/home` | HomePage | Any authenticated | Operations center: two-column view (On-Going vs Fire Out incidents), search, filtered by user's assigned region. |
| `/incidents` | IncidentsPage | Any authenticated | Incidents list with filters and role-based action buttons (Triage, Manual Entry, Import). |
| `/incidents/create` | CreatePage | ENCODER | Manual fire incident entry form using `IncidentForm`. |
| `/incidents/import` | ImportPage | ENCODER | Bulk import from XLSX/CSV: parse, validate, review, and upload bundle. |
| `/incidents/triage` | TriagePage | ENCODER / VALIDATOR | Triage queue for citizen reports; promote to official incidents. |
| `/incidents/new` | NewIncidentPage | Any authenticated | Simple map-based incident report; creates incident with PENDING status. |
| `/incidents/[id]` | IncidentDetailPage | Any authenticated | Incident detail view; validators can run conflict detection and verify/reject PENDING incidents. |
| `/admin` | — | SYSTEM_ADMIN | Redirects to `/admin/system`. |
| `/admin/system` | SystemAdminPage | SYSTEM_ADMIN | Admin hub: user management, Suricata threat log viewer, audit logs, AI analysis trigger for security alerts. |

### Frontend API Routes (Next.js Route Handlers)

| Path | Purpose |
|------|---------|
| `/api/auth/session` | Get current session from HttpOnly cookie |
| `/api/auth/sync` | Sync Keycloak access token to backend |
| `/api/auth/logout` | Clear session and logout |
