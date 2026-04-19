# Encoder → Validator Workflow — Change Log

## Summary

Implements region-scoped validator review so a `NATIONAL_VALIDATOR` can see,
accept, pend, and reject fire incidents submitted by encoders in their assigned
region — and only that region.

---

## Files Changed

| File | Type | What changed |
|---|---|---|
| `src/backend/models/fire_incident.py` | Modified | Added `PENDING_VALIDATION` to `VerificationStatus` enum; aligned `CheckConstraint` |
| `src/backend/models/incident_verification_history.py` | Rewritten | Was an empty 0-byte file; ORM model written from scratch |
| `src/backend/auth.py` | Modified | Added `get_national_validator` dependency |
| `src/backend/api/routes/regional.py` | Modified | Added two new endpoints (see below) |
| `src/postgres-init/002_validator_workflow.sql` | New | Migration SQL (idempotent) |
| `scripts/seed-dev-users.sh` | Modified | `VALIDATOR` → `NATIONAL_VALIDATOR`; validator_test assigned region 1 |
| `src/frontend/src/app/dashboard/validator/page.tsx` | New | Validator dashboard page |
| `src/frontend/src/lib/validator-api.ts` | New | Typed API helpers for new endpoints |

---

## Detailed Change Notes

### 1. `VerificationStatus` enum (fire_incident.py)

**Problem:** `PENDING_VALIDATION` was already being written to the database by
`public_dmz.py` (`verification_status = 'PENDING_VALIDATION'`) but the ORM enum
only declared `DRAFT`, `PENDING`, `VERIFIED`, `REJECTED`. Any route that loaded a
`PENDING_VALIDATION` row via the ORM would raise a validation error.

**Fix:** Added `PENDING_VALIDATION = "PENDING_VALIDATION"` and updated the
`CheckConstraint` string to match.

---

### 2. `incident_verification_history.py`

**Problem:** The file existed but was empty (0 bytes). `models/__init__.py`
imported `IncidentVerificationHistory` and `TargetType` from it, so the entire
models package failed to import at startup.

**Fix:** Wrote the full ORM model with columns that match the migration SQL
exactly:
- `history_id` — serial PK
- `target_type` — `'OFFICIAL'` or `'CIVILIAN'`
- `target_id` — FK-free integer (avoids cross-table FK complexity)
- `action_by_user_id` — UUID FK to `wims.users`
- `previous_status`, `new_status` — VARCHAR(32)
- `notes` — nullable TEXT
- `action_timestamp` — TIMESTAMPTZ default now()

---

### 3. `get_national_validator` dependency (auth.py)

**Pattern:** Exact mirror of the existing `get_regional_encoder` dependency.
Requires `NATIONAL_VALIDATOR` role and a non-null `assigned_region_id` in
`wims.users`.  Returns the user dict augmented with `assigned_region_id` so
every validator route gets region isolation for free.

**Why a separate dependency and not a shared one:** Role strings are distinct
(`REGIONAL_ENCODER` vs `NATIONAL_VALIDATOR`); merging them into one dependency
would require runtime role-checking inside the endpoint, defeating FastAPI's
declarative dependency model.

---

### 4. New endpoints (regional.py)

#### `GET /api/regional/validator/incidents`

- Auth: `get_national_validator` — only `NATIONAL_VALIDATOR` with assigned region.
- Hard filter: `fi.region_id = validator.assigned_region_id` (no override possible).
- Hard filter: `fi.encoder_id IS NOT NULL` — public DMZ submissions never appear here.
- Default statuses when no `status` param: `PENDING` and `PENDING_VALIDATION`.
- Optional filters: `status`, `encoder_id` (UUID string), `limit`, `offset`.
- Existing `GET /api/regional/incidents` for encoders is untouched.

#### `PATCH /api/regional/incidents/{incident_id}/verification`

- Auth: `get_national_validator`.
- Body: `{ "action": "accept"|"pending"|"reject", "notes": "..." }`.
- Server maps actions to DB values: `accept→VERIFIED`, `pending→PENDING`, `reject→REJECTED`.
- Five guard checks before any write:
  1. Incident exists and is not archived → 404 if not.
  2. `incident.region_id == validator.assigned_region_id` → 403 if not (returns 403, not 404, so caller knows it's a permission boundary, not a missing record).
  3. `incident.encoder_id IS NOT NULL` → 403 if null (rejects public DMZ rows).
  4. `action` is a known value → 400 if not.
  5. `current_status != target_status` → 409 if already at target (idempotency guard).
- Both the `fire_incidents` UPDATE and the `incident_verification_history` INSERT
  are in the same transaction — rollback on either failure leaves no partial state.
- Response includes `incident_id`, `previous_status`, `new_status`, `encoder_id`,
  `region_id` so the frontend can update exactly one row optimistically.

---

### 5. Migration SQL (002_validator_workflow.sql)

Idempotent — safe to re-run at any time.

Five operations, each guarded by existence checks:

1. **`users_role_check` constraint** — drops and recreates to include both `VALIDATOR`
   (legacy seed value) and `NATIONAL_VALIDATOR` (authoritative application value).
2. **Data migration** — `UPDATE wims.users SET role = 'NATIONAL_VALIDATOR' WHERE role = 'VALIDATOR'`.
3. **`validator_test` region** — sets `assigned_region_id = 1` if NULL.
4. **`fire_incidents_verification_status_check`** — rebuilt with `PENDING_VALIDATION`.
5. **`wims.incident_verification_history`** — `CREATE TABLE IF NOT EXISTS`.
6. **RLS policy `validator_update_own_region`** — `DROP POLICY IF EXISTS` then `CREATE POLICY`
   so the policy stays current on re-runs.

**RLS policy logic:**
```sql
USING (
    EXISTS (
        SELECT 1 FROM wims.users u
        WHERE  u.user_id            = current_setting('wims.current_user_id', TRUE)::uuid
          AND  u.role               = 'NATIONAL_VALIDATOR'
          AND  u.assigned_region_id = wims.fire_incidents.region_id
          AND  u.is_active          = TRUE
    )
)
```
This re-uses the same `wims.current_user_id` GUC that `database.py` already sets
via `SET LOCAL wims.current_user_id`.  `SYSTEM_ADMIN` is not constrained by this
policy — their existing unconditional policy wins via `PERMISSIVE` union.

---

### 6. `seed-dev-users.sh` fix

`VALIDATOR` → `NATIONAL_VALIDATOR` in both the `USERS` array and `ROLES` array.
`validator_test` is now assigned `region_id = 1` so the `get_national_validator`
dependency succeeds out of the box.

**Note:** After this script runs, the existing `validator_test` Keycloak role
named `VALIDATOR` must be renamed (or a new `NATIONAL_VALIDATOR` role created)
in the Keycloak realm.  The seed script now calls `kcadm.sh create roles` with
`NATIONAL_VALIDATOR` so re-running it creates the correct role.

---

### 7. Frontend (page.tsx + validator-api.ts)

- **`/dashboard/validator/page.tsx`** — client component with filter bar (status,
  encoder UUID), paginated table, and inline Accept / Pend / Reject buttons.
- On action: opens a confirmation modal with optional notes field.
- On success: optimistically updates the row's status badge in-place without
  re-fetching the full list.
- On error: surfaces the server error message inside the modal (e.g. "You do not
  have permission…" for 403, "Incident is already in status 'VERIFIED'" for 409).
- **`lib/validator-api.ts`** — typed wrappers over `apiFetch` for both endpoints.
  Import and use these in other components instead of raw `apiFetch` calls so
  response types are inferred automatically.

---

## How to Apply

```bash
# 1. Run the migration
docker compose exec -T postgres psql -U postgres -d wims \
  < src/postgres-init/002_validator_workflow.sql

# 2. Re-seed dev users (Keycloak + wims.users)
./scripts/seed-dev-users.sh

# 3. Restart backend so new ORM model is loaded
docker compose restart backend

# 4. Verify: log in as validator_test / password123
#    Navigate to /dashboard/validator
#    Should see PENDING incidents for region 1
```

---

## Acceptance Criteria Verification

| # | Criterion | Covered by |
|---|---|---|
| 1 | Encoded incidents visible to validator iff same region | `GET /validator/incidents` hard-filters `region_id`; RLS policy double-enforces on UPDATE |
| 2 | Validator actions apply only to selected incident, preserve encoder linkage | PATCH checks encoder_id IS NOT NULL before writing; response returns encoder_id |
| 3 | No cross-region leakage in list or update | List: `region_id = assigned_region_id` WHERE clause. Update: guard #2 returns 403 |
| 4 | Status transitions use existing DB options | Action map: accept→VERIFIED, pending→PENDING, reject→REJECTED |
| 5 | Verification history captures every validator action | INSERT into `incident_verification_history` in same transaction as UPDATE |

---

## Files NOT Modified

All other files are untouched:
`main.py`, `database.py`, `triage.py`, `admin.py`, `analytics.py`, `civilian.py`,
`incidents.py`, `public_dmz.py`, `ref.py`, `celery_config.py`, all model files
except the two listed above, all schemas, services, utils, and tasks.
