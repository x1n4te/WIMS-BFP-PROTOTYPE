# WIMS-BFP — Web-based Incident Management System for the Bureau of Fire Protection

A full-stack incident management platform for the Philippine Bureau of Fire Protection (BFP), featuring crowdsourced fire report triage, geospatial incident tracking, Keycloak OIDC authentication, AI-powered security threat analysis, and Suricata-based intrusion detection.

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) — system stack, data flow, Docker services, auth flow
- [API & Function Reference](docs/API_AND_FUNCTIONS.md) — backend endpoints, edge functions, frontend pages
- [Changelog](CHANGELOG.md) — version history and notable changes

## Prerequisites

- **Docker** and **Docker Compose** (v3.8+)
- **Node.js** 18+ (for local frontend development)
- **Python** 3.10+ (for local backend development)
- **Git**

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/INB-Nathan/WIMS-BFP-PROTOTYPE.git
   cd WIMS-BFP-PROTOTYPE
   ```

2. **Configure environment variables:**
   Copy the example env file if provided, or verify the dev defaults in `src/docker-compose.yml`.
   The Docker Compose file uses development placeholders — never use these in production.

3. **Start all services:**
   ```bash
   cd src
   docker-compose up --build
   ```

4. **Access the application:**
   - **Frontend:** http://localhost
   - **Keycloak Admin:** http://localhost/auth (admin / admin)
   - **Backend API:** http://localhost/api

## Environment Variables

All service configuration is managed through `src/docker-compose.yml` environment blocks. Key variables:

| Variable | Service | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | backend, celery | PostgreSQL connection string |
| `KEYCLOAK_REALM_URL` | backend | Keycloak OIDC realm endpoint |
| `KEYCLOAK_CLIENT_ID` | backend | OIDC client identifier |
| `REDIS_URL` | backend, celery | Redis broker for Celery and rate limiting |
| `OLLAMA_URL` | backend | Local LLM inference endpoint |
| `NEXT_PUBLIC_API_URL` | frontend | Backend API base URL (browser-resolvable) |
| `NEXT_PUBLIC_OIDC_AUTHORITY` | frontend | Keycloak realm URL for OIDC |

## Project Structure

```
src/
├── backend/          # FastAPI + Celery
├── frontend/         # Next.js (App Router)
├── supabase/         # Edge Functions, schema, migrations, seeds
├── postgres-init/    # DB initialization scripts
├── keycloak/         # Realm import configuration
├── suricata/         # IDS rules and logs
├── nginx/            # Reverse proxy configuration
└── docker-compose.yml
```

## Testing

**Backend (inside Docker or with dependencies installed):**
```bash
cd src/backend
pytest -v
```

**Infrastructure config tests (no Docker required):**
```bash
cd src/backend
python -m pytest tests/test_infra_config.py -v
```

## License

This project is developed for academic and government use by the Bureau of Fire Protection.
