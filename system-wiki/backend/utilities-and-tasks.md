---
title: Backend Utilities & Celery Tasks
created: 2026-05-16
updated: 2026-05-19
type: backend
tags: [wims-bfp, backend, utils, crypto, audit, session, backup, celery, exports]
sources: [src/backend/utils/, src/backend/tasks/]
status: draft
---

# Backend Utilities & Celery Tasks

## Utilities (`src/backend/utils/`)

### `crypto.py` — PII Encryption

AES-256-GCM encrypted PII blob system for `incident_sensitive_details`. PII fields (`caller_name`, `caller_number`, `owner_name`, `occupant_name`) are encrypted as a single JSON blob. PII columns in the DB are set to NULL for new writes; only the encrypted blob is authoritative.

**Configuration:** `WIMS_MASTER_KEY` env var — base64-encoded 32-byte key

**Technical details:**
- Nonce: 12 bytes (RFC 5116), fresh per `encrypt_json` call
- AAD: `"incident_id:{incident_id}"` bound to the specific record
- Deterministic JSON serialization: `json.dumps(..., sort_keys=True, separators=(",", ":"))`
- Ciphertext stored as base64; nonce stored as base64

#### Exception

`SecurityProviderError` — raised on any crypto failure (missing key, decode error, authentication failure)

#### `class SecurityProvider`

| Method | Signature | Returns | Description |
|---|---|---|---|
| `__init__(self)` | — | None | Reads `WIMS_MASTER_KEY` from env, base64-decodes, validates 32 bytes, initializes AESGCM |
| `encrypt_json(self, pii_dict, aad)` | `(dict, bytes)` | `(nonce_b64, ct_b64)` | Serializes PII dict, generates 12-byte nonce, encrypts with GCM, returns base64-encoded nonce+ciphertext |
| `decrypt_json(self, nonce_b64, ct_b64, aad)` | `(str, str, bytes)` | `dict` | Base64-decodes, validates nonce length (12), decrypts with GCM auth check, JSON-deserializes |

### `audit.py` — System Audit Trail

#### `log_system_audit(db, user_id, action_type, table_affected, record_id, request=None)`

**Parameters:**

| Name | Type | Description |
|---|---|---|
| db | Session | SQLAlchemy session |
| user_id | uuid\|str\|None | User who performed the action |
| action_type | str | Action type (CREATE_USER, PROMOTE_REPORT, etc.) |
| table_affected | str | Table name affected |
| record_id | int\|None | Primary key of affected record |
| request | Request\|None | FastAPI Request for IP + User-Agent extraction |

**Behavior:** INSERT into `wims.system_audit_trails` with `(user_id, action_type, table_affected, record_id, ip_address, user_agent, timestamp=now())`. Errors are swallowed (audit failures don't block main action). Caller must commit.

### `session.py` — Redis Session Revocation

Manages revocation timestamps per Keycloak user. Any JWT issued before the revocation timestamp is considered invalid.

**Redis config:** `REDIS_URL` env var (default `redis://redis:6379/0`)

#### `class SessionManager`

| Method | Signature | Description |
|---|---|---|
| `__init__(self)` | — | Connects to Redis, pings for connectivity. Sets `_redis=None` on failure (graceful degradation) |
| `revoke_all_sessions(self, keycloak_id)` | `str` | Writes `revoked_user:{keycloak_id}` → `int(time.time())` with TTL 43200s (12h) |
| `is_token_revoked(self, keycloak_id, iat)` | `(str, int)` → bool | Reads `revoked_user:{keycloak_id}`; returns True if `iat < revocation_time` |

**Global instance:** `session_manager = SessionManager()` — imported by admin routes.

### `backup_crypto.py` — Backup File Encryption

AES-256-GCM backup encryption using the same `WIMS_MASTER_KEY` as PII encryption. Raw binary format: `[12-byte nonce][ciphertext+tag]`. No base64 encoding on disk. File extension: `.sql.enc`

| Function | Signature | Returns | Description |
|---|---|---|---|
| `encrypt_backup(input_path, output_path=None)` | `(Path, Path\|None)` | Path | Reads SQL file, generates 12-byte nonce, encrypts with AES-256-GCM (no AAD), writes nonce+ciphertext to .sql.enc, unlinks input |
| `decrypt_backup(encrypted_path, output_path=None)` | `(Path, Path\|None)` | Path | Reads .sql.enc, splits nonce (12 bytes) + ciphertext, decrypts, writes .sql, unlinks .enc. Atomic replace via temp file |

**Errors:** `RuntimeError` on missing/too-short file or decryption failure.

---

## Celery Tasks (`src/backend/tasks/`)

### `exports.py` — Analytics Export Pipeline

Celery tasks for CSV, XLSX, and PDF exports. All use the analytics read model (`analytics_read_model.py`).

**Constants:**

| Constant | Value |
|---|---|
| `ALLOWED_EXPORT_COLUMNS` | Set of 26 whitelisted column names (no PII) |
| `DEFAULT_EXPORT_COLUMNS` | 11 default columns if whitelist result is empty |
| `EXPORT_DIR` | `/tmp/wims-exports` (overridable via `EXPORT_DIR` env) |

**Helper Functions:**

| Function | Signature | Description |
|---|---|---|
| `_serialize_value(v)` | Any → str | None→"", datetime→isoformat(), else str(v) |
| `_valid_columns(columns)` | list[str] → list[str] | Filters against ALLOWED_EXPORT_COLUMNS; falls back to DEFAULT if empty |
| `_write_csv(path, rows, columns)` | (str, list[dict], list[str]) → None | CSV with header row, utf-8 encoding |
| `_write_xlsx(path, rows, columns)` | (str, list[dict], list[str]) → None | openpyxl Workbook, sheet "Incidents" |
| `_write_pdf(path, rows, columns)` | (str, list[dict], list[str]) → None | reportlab SimpleDocTemplate, letter landscape, dark red header (#7f1d1d), 7pt font |
| `_insert_export_log(db, **kwargs)` | (Session, keyword args) → None | INSERT into `analytics_export_log` with all metadata |

**Core Export Function:**

`_export(*, task_id, user_id, filters, columns, export_format, extension, content_type, writer, incident_ids=None, export_type="analytics")` → `str`

**Behavior:** Validates/whitelists columns → opens DB session with RLS → fetches rows (get_export_rows or get_analyst_export_rows) → creates EXPORT_DIR → generates unique filename → calls writer → logs to analytics_export_log → returns file path.

**Celery Tasks:**

| Task | Name | Writer | Format | Content Type | Purpose |
|---|---|---|---|---|---|
| `export_incidents_csv_task` | `tasks.exports.export_incidents_csv` | `_write_csv` | csv | text/csv | Analytics aggregate CSV export |
| `export_incidents_pdf_task` | `tasks.exports.export_incidents_pdf` | `_write_pdf` | pdf | application/pdf | Analytics aggregate PDF export |
| `export_incidents_excel_task` | `tasks.exports.export_incidents_excel` | `_write_xlsx` | xlsx | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | Analytics aggregate XLSX export |
| `export_analyst_incidents_task` | `tasks.exports.export_analyst_incidents` | Dispatches to writer by format | csv/pdf/xlsx | Dynamic | Analyst selected/filtered export with incident_ids support; deduplicates IDs |

All tasks use `@celery_app.task(bind=True)` — `self.request.id` provides the Celery task UUID.

**File handling:** Filename pattern: `analytics_export_{uuid4_hex_12ch}.{extension}`. No cleanup mechanism — files accumulate in EXPORT_DIR. File path is persisted in `analytics_export_log` for retrieval.

### `notifications.py` — Citizen Report Push Notifications

`send_status_notification(report_id, new_status)` sends Firebase Cloud Messaging notifications to tokens registered in `wims.report_notification_tokens`.

**Runtime configuration:** Firebase Admin credentials must be injected at runtime via `FIREBASE_SERVICE_ACCOUNT_JSON` or `FIREBASE_CREDENTIALS_PATH`. Service-account JSON files are not tracked in Git.

**Dispatch behavior:** `src/backend/api/routes/triage.py` enqueues notification tasks only after promotion and analytics sync commits. Enqueue failures are logged and suppressed so a Redis/Celery broker outage does not turn a persisted promotion into a 500 response.
