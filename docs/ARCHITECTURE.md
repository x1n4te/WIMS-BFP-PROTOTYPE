# WIMS-BFP System Architecture

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | Next.js 16 (App Router), React 19, TailwindCSS 4 | Standalone output, Leaflet maps |
| **Backend** | FastAPI (Python 3.10+) | Async, Pydantic v2 |
| **Database** | PostgreSQL 15 + PostGIS 3.4 | Geography(POINT, 4326) for all spatial data |
| **Authentication** | Keycloak 24 (OIDC/JWT with PKCE) | **Supabase is strictly forbidden for auth** (see constitution) |
| **AI/ML** | Qwen2.5-3B via Ollama | Local inference for security log XAI narratives |
| **Task Queue** | Celery + Redis 7.2 | Beat scheduler for Suricata log ingestion |
| **IDS** | Suricata | Network intrusion detection, EVE JSON log output |
| **Edge Gateway** | Nginx (Alpine) | Reverse proxy, ports 80/443 |

## Key Directories

```
src/
├── backend/            # FastAPI application
│   ├── api/routes/     # HTTP route handlers (incidents, admin, civilian, triage)
│   ├── models/         # SQLAlchemy ORM models
│   ├── tasks/          # Celery background tasks (Suricata ingestion)
│   ├── auth.py         # Keycloak JWT validation + role dependencies
│   └── main.py         # App entry, middleware, router mounts
├── frontend/           # Next.js application
│   └── src/app/        # App Router pages (dashboard, incidents, admin, etc.)
├── postgres-init/      # Database initialization scripts
├── supabase/           # Edge Functions + SQL schema/migrations/seeds
│   ├── functions/      # Deno edge functions (analytics, commit, conflict, etc.)
│   ├── migrations/     # Incremental schema changes
│   ├── seeds/          # Reference data (geo hierarchy, test data)
│   └── schema_v2.sql   # Canonical schema definition
├── keycloak/           # Keycloak realm import (bfp-realm.json)
├── suricata/           # IDS rules and log mount point
│   ├── rules/          # Custom Suricata rules
│   └── logs/           # EVE JSON output (gitignored, runtime only)
└── nginx/              # Nginx gateway configuration
```

## Data Flow

The system enforces a two-tier data model with triage as the bridge:

```
┌──────────────────────────────────────────────────────────────┐
│                     COMMUNITY TIER (Unverified)              │
│  citizen_reports: crowdsourced fire reports (trust_score=0)  │
│  Submitted via POST /api/civilian/reports (no auth)          │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                        TRIAGE LAYER                          │
│  ENCODER/VALIDATOR reviews pending reports                   │
│  GET /api/triage/pending → POST /api/triage/{id}/promote    │
│  Conflict detection checks for duplicates (2hr window,      │
│  same region/city/barangay)                                  │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                 OFFICIAL TIER (Verified — SSOT)              │
│  fire_incidents: verified incidents with PostGIS location    │
│  incident_verification_history: chain-of-custody audit       │
│  Status: DRAFT → PENDING → VERIFIED (or REJECTED)           │
│  Soft-delete only (is_archived = TRUE), never hard-delete    │
└──────────────────────────────────────────────────────────────┘
```

## Docker Services

All services run on the `wims_internal` bridge network.

| Service | Image | Role |
|---------|-------|------|
| **postgres** | `postgis/postgis:15-3.4-alpine` | Primary database with PostGIS. Init scripts from `postgres-init/` and `supabase/schema_v2.sql`. |
| **redis** | `redis:7.2-alpine` | Celery broker and rate-limit store. |
| **keycloak** | `quay.io/keycloak/keycloak:24.0.0` | OIDC identity provider. Imports `bfp-realm.json` on startup. Uses Postgres for its own DB. |
| **ollama** | `ollama/ollama:latest` | Local LLM inference (Qwen2.5-3B). 2 CPU / 4 GB memory limit. |
| **backend** | Build from `./backend` | FastAPI app. Connects to Postgres, Redis, Keycloak, Ollama. |
| **celery-worker** | Build from `./backend` | Celery worker + beat. Ingests Suricata EVE logs every 10s. |
| **frontend** | Build from `./frontend` | Next.js standalone. Proxied through Nginx. |
| **wims-suricata** | `jasonish/suricata:latest` | Network IDS. Sniffs `eth0` on the Docker bridge. Logs to `suricata/logs/`. |
| **nginx-gateway** | `nginx:alpine` | Edge gateway. Exposes ports 80 and 443. Routes to frontend, backend, and Keycloak. |

## Authentication Flow

1. User clicks Login on the frontend.
2. Frontend redirects to Keycloak with PKCE challenge (`oidc-client-ts`).
3. Keycloak authenticates the user and redirects back to `/callback` with an authorization code.
4. Frontend calls `POST /api/auth/callback` with the code and code verifier.
5. Backend exchanges the code with Keycloak for tokens and upserts the user in `wims.users`.
6. Access token is stored in an HttpOnly cookie and used for subsequent API requests.
7. Protected backend routes validate the JWT via `get_current_user` / `get_current_wims_user` / `get_system_admin`.

## User Roles

| Role | Capabilities |
|------|-------------|
| **ENCODER** | Create incidents, import bulk data, access triage queue |
| **VALIDATOR** | Verify/reject incidents, promote citizen reports, run conflict detection |
| **ANALYST** | View analytics summaries |
| **ADMIN** | All of the above + user management |
| **SYSTEM_ADMIN** | Full system access: user management, security threat logs, audit trails, AI analysis |

## Security Architecture

- **Suricata IDS** monitors the Docker bridge network for threats (e.g., False Data Injection).
- **Celery beat** ingests Suricata EVE logs into `security_threat_logs` every 10 seconds.
- **AI Analysis:** SYSTEM_ADMIN can trigger Qwen2.5-3B via Ollama to generate XAI narratives explaining why a packet was flagged.
- **Rate limiting:** Redis sliding-window rate limiter on `POST /api/auth/login` (5 requests per 900s window).
- **Immutability Law:** Core tables use soft-delete (`is_archived`) — no hard deletes permitted. Every verification action is logged in `incident_verification_history` with the acting `user_id`.
