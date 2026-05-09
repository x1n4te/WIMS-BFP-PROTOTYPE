# M4: Incident Workflow (REGIONAL_ENCODER + NATIONAL_VALIDATOR)

**Status:** In Progress — 7 of 9 original issues complete; 2 partial; 4 enhancements added beyond spec
**Open Issues:** 2 (M4-B partial, M4-E partial)
**Closed Issues:** 7
**Created:** 2026-04-27
**Updated:** 2026-05-10

---

## Milestone Overview

End-to-end incident lifecycle from encoding through verification. This milestone covers the complete workflow for Regional Encoders to create and edit incidents, and National Validators to review and approve them.

**Key Stakeholders:**
- **REGIONAL_ENCODER**: Creates, imports, and edits incidents
- **NATIONAL_VALIDATOR**: Reviews, approves, rejects, archives, and audits incidents

---

## Implementation Status

| Issue | Title | Status |
|-------|-------|--------|
| M4-A | Incident Creation with PostGIS Location | ✅ Complete |
| M4-B | Incident Edit (Own, Non-Verified Only) | ⚠️ Partial |
| M4-C | AFOR Spreadsheet Import | ✅ Complete |
| M4-D | Duplicate Detection on Import | ⚠️ Partial |
| M4-E | Draft Save | ⚠️ Partial |
| M4-F | National Validator Verification Queue | ✅ Complete + Enhanced |
| M4-G | Side-by-Side Diff View | ✅ Complete + Enhanced |
| M4-H | Bulk Approve | ✅ Complete |
| M4-I | Validator Audit Trail Viewer | ✅ Complete |
| — | Duplicate Detection System (Encoder + Validator) | ✅ Added (beyond spec) |
| — | Incident Archive & REPLACED Status | ✅ Added (beyond spec) |
| — | Reference Number Generation | ✅ Added (beyond spec) |

---

## Issues Detail

### M4-A: Incident Creation with PostGIS Location
**Priority:** High | **Status:** ✅ Complete

#### Implemented
- `POST /api/regional/incidents` — creates incident with full AFOR form data
- `fi.location` stored as `ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography`
- MapPickerInner component with pin-drop, search bar, and read-only view mode
- Full AFOR form covering all required sections (A–L): alarm timeline, personnel, damage, narrative
- Draft → Submit → PENDING → VERIFIED lifecycle fully wired
- Reference number generated on first VERIFIED transition (format: `AFOR-RGN-{region}-{station}-{type}-{month/year}-{seq}`)
- All timestamps stored UTC, displayed in Asia/Manila (PHT) via `toLocaleString('en-PH', { timeZone: 'Asia/Manila' })`

#### Exit Criteria
- [x] Encoder can create incident with map-picked coordinates
- [x] Incident appears in regional incident list

---

### M4-B: Incident Edit (Own, Non-Verified Only)
**Priority:** High | **Status:** ⚠️ Partial

#### Implemented
- `PATCH /api/regional/incidents/{id}` with full AFOR field updates
- Edit mode on `/dashboard/regional/incidents/[id]` — edit icon visible only to encoder for non-VERIFIED incidents
- IncidentForm component with `initialData` hydration; time fields loaded from `alarm_timeline._response` JSONB

#### Missing / Gaps
- **No backend encoder ownership check** — `update_incident()` does not assert `encoder_id = current_user`. Ownership is enforced only at the UI layer; a malicious encoder with a known `incident_id` could edit another encoder's incident via direct API call.
- **Edit does not create audit trail entry** — `incident_verification_history` is only written on status transitions, not on field edits. Compliance gap.
- **Time fields edge case** — `time_engine_dispatched`, `time_arrived_at_scene`, `time_returned_to_base` are stored inside `alarm_timeline._response` JSONB (not dedicated columns). Old incidents imported before this structure existed will show blank time fields in edit mode consistently.

#### Planned Fixes
```
Backend — update_incident():
  Add WHERE encoder_id = CAST(:uid AS uuid) to the UPDATE
  and raise 403 if rowcount == 0 (no match = not owner)

Backend — update_incident():
  After the UPDATE, INSERT into incident_verification_history
  with action_label = 'EDITED', previous_status = current_status,
  new_status = current_status (status unchanged, just fields changed)
```

#### Exit Criteria
- [x] Encoder can edit their own non-VERIFIED incidents
- [x] Encoder cannot edit VERIFIED incidents (UI guard)
- [ ] Backend rejects edits from non-owner encoders (403)
- [ ] Edit creates audit trail entry

---

### M4-C: AFOR Spreadsheet Import
**Priority:** High | **Status:** ✅ Complete

#### Implemented
- `POST /api/regional/incidents/import` — multipart/form-data xlsx upload
- Parser: `parse_wildland_afor_report_data` and structural AFOR formats
- Response: `{created, updated, duplicates, errors: [{row, message}]}`
- `/afor/import` page with drag-and-drop upload and import summary table

#### Exit Criteria
- [x] Encoder can import AFOR xlsx and see summary
- [x] Import errors shown per row

---

### M4-D: Duplicate Detection on Import
**Priority:** High | **Status:** ⚠️ Partial

#### Implemented
- Import pipeline calls `check_for_duplicate()` before committing each row
- Duplicate rows are counted in the summary response under `duplicates`
- Skip behavior is the default (duplicate rows are not imported)

#### Missing / Gaps
- **No per-row UI decision** — encoder cannot currently choose skip / merge / force-create on a per-row basis. All duplicates are silently skipped. The spec calls for a confirmation modal before commit.

#### Planned Fix
```
Frontend — /afor/import:
  When response.duplicates > 0, show a review modal listing duplicate rows
  with checkboxes: Skip | Merge (update existing) | Force Create
  Re-submit with per-row decisions included in request body

Backend — import endpoint:
  Accept optional per_row_decisions: {row_number: "skip"|"merge"|"force"} parameter
  Implement merge path: UPDATE existing incident with imported values
```

#### Exit Criteria
- [x] Import detects duplicates
- [x] Duplicate rows reported in summary
- [ ] Encoder chooses skip / merge / force per duplicate before commit

---

### M4-E: Draft Save
**Priority:** Medium | **Status:** ⚠️ Partial

#### Implemented
- `POST /api/regional/incidents` with `verification_status = DRAFT` on initial save
- `GET /api/regional/incidents/drafts` — encoder's own drafts only
- `PATCH /api/regional/incidents/{id}` — update draft fields
- `POST /api/regional/incidents/{id}/submit` — transition DRAFT → PENDING
- `/dashboard/regional/drafts` list page
- Drafts excluded from validator queue (`status != DRAFT` filter)

#### Missing / Gaps
- **No Celery auto-expiry** — drafts do not expire after 30 days. A `tasks/draft_expiry.py` Celery periodic task is required to `UPDATE ... SET verification_status = 'REJECTED'` (or delete) drafts older than 30 days.

#### Planned Fix
```
Backend — tasks/draft_expiry.py (new file):
  @celery_app.task
  def expire_old_drafts():
      db.execute(UPDATE wims.fire_incidents
                 SET verification_status = 'REJECTED', updated_at = NOW()
                 WHERE verification_status = 'DRAFT'
                   AND created_at < NOW() - INTERVAL '30 days')

Backend — celery_config.py:
  Add beat_schedule entry for expire_old_drafts every 24 hours
```

#### Exit Criteria
- [x] Encoder can save and resume drafts
- [x] Drafts do not appear in validator queue
- [ ] Drafts auto-expire after 30 days (Celery task not yet implemented)

---

### M4-F: National Validator Verification Queue
**Priority:** High | **Status:** ✅ Complete + Enhanced

#### Implemented (original spec)
- `GET /api/regional/validator/incidents` — **cross-region** (all regions, not just assigned)
- `PATCH /api/regional/incidents/{id}/verification` — accept / reject / pending actions
- Audit trail entry per action via `incident_verification_history`
- `/dashboard/validator` queue page with filters, pagination, status badges

#### Implemented (enhancements beyond spec)
- **Status values extended:** `REPLACED` added alongside `DRAFT`, `PENDING`, `PENDING_VALIDATION`, `VERIFIED`, `REJECTED`
- **action_label column** on `incident_verification_history` — human-readable label per action (`APPROVED`, `REJECTED`, `BULK_APPROVED`, `REPLACED_EXISTING`, `ACCEPTED_AS_NEW`, `ARCHIVED`, `EDITED`)
- **Archive endpoint:** `PATCH /api/regional/validator/incidents/{id}/archive` — archives VERIFIED / REJECTED / REPLACED incidents; requires `archived_at` column
- **Archived tab:** filter `?archived=true` shows only archived incidents; no action buttons
- **Conditional action buttons:** finalized incidents (VERIFIED / REJECTED / REPLACED) show Archive only; pending incidents show Accept + Reject
- **DUPLICATE badge** — shown on PENDING incidents with `is_duplicate = TRUE`
- **Newest-first sort** on queue (previously oldest-first)
- **Submitted column** — leftmost data column showing `created_at` in PHT
- **Direct Accept flow** — clicking Accept immediately calls the backend (no intermediate Confirm step). If backend returns 409 DUPLICATE\_DETECTED, the side-by-side resolution modal appears automatically.
- **Bulk confirm modal** — replaced `window.confirm()` with an in-app modal

#### Exit Criteria
- [x] Validator sees cross-region queue
- [x] Validator can approve or reject with reason
- [x] Each action creates audit trail entry with action_label
- [x] VERIFIED / REJECTED incidents can be archived
- [x] Archived incidents visible in separate tab

---

### M4-G: Side-by-Side Diff View
**Priority:** Medium | **Status:** ✅ Complete + Enhanced

#### Implemented (original spec)
- `GET /api/regional/validator/incidents/{id}/diff` — returns original snapshot vs current field values
- `UpdateRequestDiffPanel` component — renders two-column field-by-field comparison with changed fields highlighted
- Used in validator queue action modal for update requests (`parent_incident_id` set)

#### Implemented (enhancements beyond spec)
- **Duplicate resolution modal** — when the validator clicks Accept on any incident, the backend runs `check_for_duplicate()`. If a match is found (409), a full side-by-side modal appears showing the PENDING incident vs the matched VERIFIED incident.
- **4 resolution options in modal:**
  - **Replace Existing** — verifies the new incident with the original's reference number; marks the old incident as `REPLACED` + `is_archived = TRUE`
  - **Verify as New** — verifies with a brand-new reference number; `force = true` bypasses the duplicate check
  - **Reject** — opens the rejection notes flow
  - **Cancel** — keeps incident as PENDING for further review
- **Auto-show on detail page** — when a validator opens a duplicate-flagged incident (`is_duplicate = TRUE, duplicate_of` set), the side-by-side modal appears automatically

#### Exit Criteria
- [x] Validator sees what changed before approving (update requests)
- [x] Validator sees side-by-side comparison for duplicate incidents before accepting
- [x] Validator has 4 resolution options for duplicates

---

### M4-H: Bulk Approve
**Priority:** Medium | **Status:** ✅ Complete

#### Implemented
- Checkbox selection on all PENDING incidents in the queue
- Select-all for PENDING checkbox in table header
- `POST /api/regional/validator/incidents/bulk-approve` with `{incident_ids: [int]}`
- Processes incidents in chronological order (`created_at ASC`) to preserve temporal integrity
- Per-incident `check_for_duplicate()` call during bulk with `verified_window_seconds=60` guard
- `held_for_review: [{id, matching_incident_id}]` in response for mid-batch duplicates
- **Bulk confirm modal** (in-app, not `window.confirm`) showing count before execution
- Response shape: `{approved: N, incident_ids: [...], held_for_review: [...]}`
- `action_label = 'BULK_APPROVED'` in audit trail

#### Note on atomicity
The implementation is **sequential per-incident** rather than all-or-nothing. A failure mid-batch will leave earlier incidents approved. True atomicity would require wrapping all approvals in a single DB transaction with rollback — not currently implemented.

#### Exit Criteria
- [x] Validator can select multiple incidents and approve in one click
- [x] In-app confirmation modal (not browser dialog)
- [x] Chronological processing order
- [x] Mid-batch duplicates held for review, not silently approved
- [ ] All-or-nothing atomicity (partial failure rolls back approved items)

---

### M4-I: Validator Audit Trail Viewer
**Priority:** Medium | **Status:** ✅ Complete

#### Implemented
- `GET /api/regional/validator/audit-logs` with filters: `date_from`, `date_to`, `region_id`, `encoder_id`
- `GET /api/regional/validator/audit-logs/export` — CSV download with date-stamped filename
- Response fields: `incident_id`, `previous_status`, `new_status`, `action_by_user_id`, `actor_username` (resolved), `region_display` (resolved region name), `action_label`, `notes`, `action_timestamp`
- `/dashboard/validator/audit` page with filter form, paginated table, and Export CSV button
- Table columns: **Date & Time** | **Incident** | **Region** | **By** | **Action**

#### Exit Criteria
- [x] Validator can search audit trail by date, region, encoder
- [x] Validator can export as CSV
- [x] Action labels are human-readable (not raw status codes)
- [x] Actor shown as username, not UUID

---

## Enhancements Added Beyond Original Spec

### EXT-1: Duplicate Detection System
**Status:** ✅ Complete

A dedicated `services/duplicate_detection.py` service implements spatial + temporal duplicate matching used across multiple call sites.

#### Detection Logic
- **Primary check:** `ST_DWithin(fi.location::geography, point, 5000)` (5 km radius) + same `region_id` + not archived + `verification_status NOT IN (DRAFT, REJECTED, REPLACED)`
- **Date filter (optional):** When `notification_dt` is available, match within ±1 day in Asia/Manila timezone. When absent, date filter is skipped (spatial-only match).
- **Fallback:** When no lat/lon available, match on `region_id` + `general_category` OR `incident_type_code` with same optional date window.
- **Update request exclusion:** Incidents with `parent_incident_id` set are excluded from the validator-side duplicate check (the parent is intentionally at the same location).

#### Encoder-side (submission)
- `POST /api/regional/incidents/{id}/submit` calls `check_for_duplicate()` before transitioning to PENDING
- Returns `HTTP 409 {code: "DUPLICATE_DETECTED", matched_incident_id, matched_status}`
- Frontend modal: **Submit Anyway** (force) | **View Existing** | **Edit Incident** | **Cancel**
- `force=true` query param bypasses the check; `is_duplicate` stays `FALSE`
- `ack_duplicate=true` (legacy path) also bypasses but sets `is_duplicate=TRUE, duplicate_of=<id>`

#### Validator-side (accept)
- `PATCH /api/regional/incidents/{id}/verification?action=accept` (no force) triggers `check_for_duplicate()`
- Returns `HTTP 409 {code: "DUPLICATE_DETECTED", matched_incident_id}` when match found
- Frontend: clicking **Accept** immediately calls the backend. On 409, the side-by-side modal auto-opens with 4 resolution options.
- `force=true` bypasses check for the Verify as New / Replace Existing decisions

---

### EXT-2: Incident Archive & REPLACED Status
**Status:** ✅ Complete

#### Schema additions
- `wims.fire_incidents.archived_at TIMESTAMPTZ` — set when `is_archived` transitions to TRUE
- `verification_status` CHECK constraint expanded to include `'REPLACED'`
- `incident_verification_history.action_label VARCHAR(80)` — human-readable per-action label

#### Behavior
- Archive endpoint: `PATCH /api/regional/validator/incidents/{id}/archive`
  - Allowed only when `verification_status IN (VERIFIED, REJECTED, REPLACED)`
  - Sets `is_archived = TRUE, archived_at = NOW()`
  - Writes audit trail entry with `action_label = 'ARCHIVED'`
- REPLACED status: when validator chooses "Replace Existing" in the duplicate modal, the original incident is set to `verification_status = 'REPLACED', is_archived = TRUE`
- Archived incidents visible in `/dashboard/validator` via the **Archived** tab filter (`?archived=true`)

---

### EXT-3: Reference Number Generation
**Status:** ✅ Complete

Reference numbers are generated on first `VERIFIED` transition.

#### Format
```
AFOR-RGN-{REGION_CODE}-{STATION_ABBREVIATION}-{TYPE_CODE}-{MON_YEAR}-{SEQ:04d}
```
Example: `AFOR-RGN-NCR-TBA-APT-MAR-2026-0001`

- Sequence is per `(region_code, station_abbr, type_code, month_year)` group
- Replace Existing inherits the original incident's reference number
- Update request approval inherits the parent's reference number

---

## Database Schema Summary

### Status Values (current)
| Status | Description |
|--------|-------------|
| `DRAFT` | Encoder working on incident, not yet submitted |
| `PENDING` | Submitted for validation |
| `PENDING_VALIDATION` | Public DMZ / system-submitted, awaiting triage |
| `VERIFIED` | Approved by validator; reference number assigned |
| `REJECTED` | Rejected with reason |
| `REPLACED` | Superseded by a newer verified incident |

### Key Columns (wims.fire_incidents)
| Column | Type | Description |
|--------|------|-------------|
| `verification_status` | VARCHAR | One of the 6 statuses above |
| `is_archived` | BOOLEAN | Soft-delete flag |
| `archived_at` | TIMESTAMPTZ | When archived |
| `is_duplicate` | BOOLEAN | Set by ack_duplicate path |
| `duplicate_of` | INTEGER FK | Points to matched incident |
| `parent_incident_id` | INTEGER FK | Set for update requests |
| `reference_number` | VARCHAR | AFOR format, assigned on VERIFIED |
| `location` | GEOGRAPHY(Point,4326) | PostGIS coordinates |

### Key Audit Events (action_label values)
| Label | Trigger |
|-------|---------|
| `SUBMITTED` | Encoder submits DRAFT → PENDING |
| `APPROVED` | Validator accepts → VERIFIED |
| `REJECTED` | Validator rejects |
| `BULK_APPROVED` | Validated via bulk approve |
| `REPLACED_EXISTING` | accept_replace — new supersedes old |
| `ACCEPTED_AS_NEW` | force accept bypassing duplicate |
| `ARCHIVED` | Validator archives finalized incident |
| `EDITED` | *(planned — not yet implemented)* Encoder edits fields |

---

## Frontend Routes (current)

| Route | Role | Purpose |
|-------|------|---------|
| `/dashboard/regional` | REGIONAL_ENCODER | Incident list with location + updated_at |
| `/dashboard/regional/incidents/[id]` | REGIONAL_ENCODER / NATIONAL_VALIDATOR | View, edit, submit, validate |
| `/dashboard/regional/drafts` | REGIONAL_ENCODER | Draft list |
| `/afor/import` | REGIONAL_ENCODER | AFOR xlsx bulk import |
| `/dashboard/validator` | NATIONAL_VALIDATOR | Verification queue + archive tab |
| `/dashboard/validator/audit` | NATIONAL_VALIDATOR | Audit trail with CSV export |

---

## Remaining Work

### Short-term (blocking compliance / correctness)

#### 1. Backend encoder ownership check in `update_incident()`
```python
# Add to PATCH /api/regional/incidents/{id}
WHERE incident_id = :iid AND encoder_id = CAST(:uid AS uuid)
# Raise 403 if rowcount == 0
```

#### 2. Audit trail entry on incident edit
```python
# After UPDATE in update_incident(), insert:
INSERT INTO wims.incident_verification_history (
    incident_id, action_by_user_id, previous_status, new_status, action_label
) VALUES (:iid, :uid, :status, :status, 'EDITED')
```

### Medium-term

#### 3. Celery draft auto-expiry (M4-E gap)
New file `src/backend/tasks/draft_expiry.py`:
```python
@celery_app.task
def expire_old_drafts():
    db.execute("""
        UPDATE wims.fire_incidents
        SET verification_status = 'REJECTED', updated_at = NOW()
        WHERE verification_status = 'DRAFT'
          AND created_at < NOW() - INTERVAL '30 days'
    """)
```
Add to `celery_config.py` beat schedule.

#### 4. AFOR import per-row duplicate decision UI (M4-D gap)
When `response.duplicates > 0`, show a review step in `/afor/import` where the encoder can choose Skip | Merge | Force Create per row before the import is committed.

### Long-term / Nice-to-have

#### 5. Bulk approve atomicity
Wrap all per-incident approvals in a single DB transaction so a mid-batch failure rolls back previously approved incidents.

#### 6. Incident edit version history
Store a full JSON snapshot of `incident_nonsensitive_details` before each edit in a separate `incident_edit_history` table for complete field-level change tracking.

---

## API Endpoints Reference

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/regional/incidents` | ENCODER | Create incident (DRAFT) |
| GET | `/regional/incidents` | ENCODER | List own incidents |
| PATCH | `/regional/incidents/{id}` | ENCODER | Edit incident fields |
| POST | `/regional/incidents/{id}/submit` | ENCODER | Submit DRAFT → PENDING |
| POST | `/regional/incidents/import` | ENCODER | Bulk AFOR xlsx import |
| GET | `/regional/incidents/drafts` | ENCODER | List own drafts |
| GET | `/regional/validator/incidents` | VALIDATOR | Cross-region queue |
| PATCH | `/regional/incidents/{id}/verification` | VALIDATOR | Accept / reject / pending |
| POST | `/regional/validator/incidents/bulk-approve` | VALIDATOR | Bulk accept |
| PATCH | `/regional/validator/incidents/{id}/archive` | VALIDATOR | Archive finalized incident |
| GET | `/regional/validator/incidents/{id}/diff` | VALIDATOR | Side-by-side diff |
| GET | `/regional/validator/audit-logs` | VALIDATOR | Audit trail |
| GET | `/regional/validator/audit-logs/export` | VALIDATOR | CSV export |
