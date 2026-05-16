---
title: Infrastructure Configuration
created: 2026-05-16
updated: 2026-05-16
type: architecture
tags: [wims-bfp, docker, nginx, suricata, keycloak, infrastructure]
sources: [src/docker-compose.yml, src/nginx/, src/suricata/, src/keycloak/bfp-realm.json]
status: draft
---

# Infrastructure Configuration

## Docker Compose

**File:** `src/docker-compose.yml`

**Network:** `wims_internal` (bridge driver)

**Services:**

| Service | Container Name | Image | Ports |
|---|---|---|---|
| postgres | wims-postgres | `postgis/postgis:15-3.4-alpine` | 5432 |
| redis | wims-redis | `redis:7.2-alpine` | 6379 |
| mailhog | wims-mailhog | `mailhog/mailhog:v1.0.1` | 1025 (SMTP), 8025 (Web UI) |
| keycloak | wims-keycloak | `quay.io/keycloak/keycloak:24.0.0` | (none exposed) |
| backend | wims-backend | Dockerfile at `./backend/Dockerfile` (python:3.11-slim) | 8000 (internal) |
| frontend | wims-frontend | `./frontend/Dockerfile` (Next.js) | 3000 (internal) |
| wims-suricata | wims-suricata | `jasonish/suricata:latest` | (none) |
| nginx-gateway | wims-nginx-gateway | `nginx:alpine` | 80, 443 |

**Health checks:** postgres (`pg_isready -U postgres -d wims`, interval 5s), redis (`redis-cli ping`, interval 5s). Backend depends on both service_healthy.

**Named volumes:** `postgres_data`, `ollama_data`, `incident_attachments_data`

**Key env vars (backend):**

| Variable | Default |
|---|---|
| `DATABASE_URL` | `postgresql://postgres:password@postgres:5432/wims` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `KEYCLOAK_REALM_URL` | `http://keycloak:8080/auth/realms/bfp` |
| `KEYCLOAK_ISSUER` | `http://localhost/auth/realms/bfp` |
| `KEYCLOAK_CLIENT_ID` | `wims-web` |
| `KEYCLOAK_ADMIN_USER` | `admin` |
| `KEYCLOAK_ADMIN_PASSWORD` | `admin` |
| `OLLAMA_URL` | `http://ollama:11434` |
| `SURICATA_EVE_PATH` | `/var/log/suricata/eve.json` |
| `EXPORT_DIR` | `/app/storage/exports` |
| `BACKUP_DIR` | `/app/storage/backups` |

---

## Nginx

**File:** `src/nginx/nginx.conf`

**Route Table:**

| Location | Proxy Target | Purpose |
|---|---|---|
| `/api/auth/` | `http://frontend:3000` | Auth routes (session, callback, logout) handled by Next.js |
| `/api/` | `http://backend:8000` | Main API backend with CORS + cookie domain rewrite |
| `/auth/` | `http://keycloak:8080/auth/` | Keycloak authentication (with X-Forwarded-Host/Port) |
| `/` | `http://frontend:3000/` | All other traffic to Next.js |

**Key config points:**
- `client_max_body_size 50M`
- OPTIONS preflight handled directly by nginx (returns 204), not proxied to backend
- CORS: dynamic `Access-Control-Allow-Origin: $http_origin`
- Cookie domain rewrite: `proxy_cookie_domain nginx-gateway localhost` — rewrites backend's `Domain=nginx-gateway` to `Domain=localhost` so the browser accepts it
- **No SSL/TLS** in prototype (port 443 section commented out)
- **No WebSocket/SSE** specific proxy settings (no `proxy_http_version 1.1`, no Upgrade header)
- **No caching, rate limiting, or security headers** at nginx level (beyond CORS)

---

## Suricata IDS

**Container:** `jasonish/suricata:latest` with `-i eth0`

**Directories:**
- `src/suricata/logs/` → `/var/log/suricata/` — EVE JSON output, fast.log, stats.log
- `src/suricata/rules/` → `/var/lib/suricata/rules/` — only `classification.config` present (no .rules files)

**EVE output** is consumed by the backend service via `SURICATA_EVE_PATH=/var/log/suricata/eve.json`. The backend reads `eve.json` for real-time event ingestion via `services/suricata_ingestion.py`.

**Note:** No custom `suricata.yaml` exists — the container uses its built-in default configuration. The compose file notes this is for prototype only; production would use `network_mode: "host"`.

---

## Keycloak Realm

**File:** `src/keycloak/bfp-realm.json` (~2641 lines)

Full Keycloak realm export for the `bfp` realm.

### Realm Settings

| Setting | Value |
|---|---|
| Realm ID | `bfp` |
| Display Name | `BFP` |
| Default Signature Algorithm | RS256 |
| Login Theme | `wims-bfp` (custom) |
| Reset Password Allowed | true |
| Edit Username Allowed | false |
| Revoke Refresh Token | false |
| Refresh Token Max Reuse | 0 |

### Session & Token Timeouts

| Setting | Value | Human |
|---|---|---|
| `accessTokenLifespan` | 300 | 5 min |
| `ssoSessionIdleTimeout` | 1800 | 30 min |
| `ssoSessionMaxLifespan` | 28800 | 8 hours |
| `actionTokenGeneratedByUserLifespan` | 300 | 5 min |

**Note:** 5-min access token + aggressive SSO idle timeout (30 min) explains the fast-logout bug (F-04).

### Brute Force Protection

`bruteForceProtected=true`, `permanentLockout=false`, `failureFactor=5` attempts, `waitIncrementSeconds=300` (5 min escalations).

### TOTP Policy

| Setting | Value |
|---|---|
| Type | `totp` |
| Algorithm | HmacSHA1 |
| Digits | 6 |
| Period | 30 seconds |
| Look-ahead window | 1 |
| Code reusable | false |

### Password Policy

`length(12) and upperCase(1) and lowerCase(1) and digits(1) and specialChars(1)`

### SMTP

MailHog local development: host=`mailhog`, port=`1025`, from=`noreply@wims-bfp.local`

### Roles

| Role | Description |
|---|---|
| `REGIONAL_ENCODER` | Regional encoder |
| `NATIONAL_VALIDATOR` | National validator |
| `NATIONAL_ANALYST` | National analyst |
| `SYSTEM_ADMIN` | System administrator |
| `VALIDATOR` | Legacy validator alias |
| `ANALYST` | Legacy analyst alias |

### Clients

| Client ID | Type | Auth Flow | Notes |
|---|---|---|---|
| `wims-web` | Public | Standard + PKCE S256 | Main frontend OIDC client; has audience mapper for `wims-web` |
| `wims-admin-service` | Confidential | Direct Grant + Service Account | Backend-to-Keycloak service client; hardcoded secret |
| `bfp-client` | Public | Standard + Direct Grant | Alternative/legacy client without PKCE |

### Authentication Flows

**Browser Flow:** Cookie check (ALTERNATIVE) → Username/Password form (REQUIRED) → Conditional OTP sub-flow (REQUIRED):
  - `conditional-user-configured` (ALTERNATIVE) — skip if user has no TOTP
  - `otp-role-system-administrator` (ALTERNATIVE) — requires OTP if role = system_administrator
  - `otp-role-national-validator` (ALTERNATIVE) — requires OTP if role = national_validator
  - `auth-otp-form` with `otpRememberDeviceFor=7d` (REQUIRED) — 7-day trusted device

**Reset Credentials Flow:** Choose user → Email via Mailhog → Reset password → Conditional OTP (if user has TOTP)

### Seed Test Users

All use password `WimsBFP2026!`:

| Username | Email | Role |
|---|---|---|
| `encoder_test` | encoder@bfp.gov.ph | REGIONAL_ENCODER |
| `validator_test` | validator@bfp.gov.ph | NATIONAL_VALIDATOR |
| `analyst_test` | analyst@bfp.gov.ph | NATIONAL_ANALYST |
| `analyst1_test` | analyst1_test@gmail.com | NATIONAL_ANALYST |
| `admin_test` | admin@bfp.gov.ph | SYSTEM_ADMIN |
| `encoder_r02` through `encoder_r18` | encoder_r{02-18}@bfp.gov.ph | REGIONAL_ENCODER |

### Key Security Headers

`X-Content-Type-Options: nosniff`, `Content-Security-Policy: frame-src 'self'; frame-ancestors 'self'; object-src 'none'`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`
