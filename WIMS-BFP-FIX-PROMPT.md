# WIMS-BFP Fix & M4 Verification Prompt
### Target: Claude Code | Stack: FastAPI + Next.js 16 + PostGIS + Keycloak

---

```
You are a senior full-stack engineer working on the WIMS-BFP (Wildland Incident Management System – Bureau of Fire Protection) project. You have complete access to the repository.

<context>
Stack: FastAPI (Python), Next.js 16 / React 19 / TypeScript / TailwindCSS 4, PostgreSQL 15 + PostGIS 3.4, Keycloak 24 (JWT/OIDC), Celery + Redis, Docker Compose.
Key roles: REGIONAL_ENCODER, NATIONAL_VALIDATOR, SYSTEM_ADMIN.
Verification status values in use: DRAFT, PENDING, PENDING_REVIEW, VERIFIED, REJECTED.
All timestamps MUST be stored and retrieved in UTC; display in Asia/Manila (PHT) where shown to users.
RLS is enforced via SET LOCAL wims.current_user_id. Do not bypass it.
PII fields use AES-256-GCM encryption via src/backend/utils/crypto.py. Never write plaintext PII.
Do NOT modify: main.py router registrations, Keycloak realm JSON, Docker Compose service topology, Suricata rules, or analytics routes — unless a fix below explicitly targets them.
After each completed fix group, output: ✅ [Group label] — what was changed and in which files.
Stop and ask before any destructive schema migration or data deletion.
</context>

<task>
Execute every fix below in order. Each group is self-contained. Do not batch unrelated groups. Confirm each group's exit criteria before moving to the next.
</task>

---

## GROUP A — ENCODING FIXES

### A1 · Time-of-notification timezone bug
**Problem:** User inputs 2:22 PM; the system stores 10:22:00 PM.
**Root cause:** Time value is likely being parsed as UTC then displayed as PHT, or the frontend is submitting a 12-hour string without AM/PM normalization before conversion.
**Fix:**
- Locate the frontend field for "time of notification" (likely in `src/frontend/src/app/incidents/create/page.tsx` or `WildlandAforManualForm.tsx`).
- Change the input to `type="time"` using 24-hour format (HH:MM). Do not use a 12-hour picker — this eliminates AM/PM ambiguity entirely while remaining easy to input.
- On submit, combine the date and time fields into a full ISO 8601 UTC datetime string before sending to the backend. Use `new Date(\`\${date}T\${time}:00\`).toISOString()` only if the user's local time is already correctly resolved. If the system is PHT-only, treat the input as PHT and convert: offset by +08:00 before serializing.
- On the backend (`src/backend/api/routes/regional.py`), ensure the field is stored as TIMESTAMPTZ and never coerced by Python's datetime.fromisoformat without timezone awareness.
- Display the time back to the user in PHT (Asia/Manila) formatted as 24-hour HH:MM.

**Exit criteria:** Enter 14:22 → stored value is 06:22:00+00 in DB → displayed back as 14:22 PHT.

---

### A2 · Location field always shows N/A
**Problem:** The location field on incidents always displays "N/A" instead of "Region, Province/State, City".
**Fix:**
- Find where the location string is assembled for display (search for "N/A" in `src/frontend/src/`).
- The backend stores geometry as a PostGIS POINT. Reverse-geocoding to Region/Province/City must come from the `wims.reference_cities` table (populated by `scripts/reseed-reference-cities.sh`), not from an external API.
- In `GET /api/regional/incidents` and `GET /api/regional/incidents/{id}` (in `src/backend/api/routes/regional.py`), perform a spatial lookup: `SELECT rc.region_name, rc.province, rc.city FROM wims.reference_cities rc ORDER BY rc.geom <-> fi.location LIMIT 1` to resolve the nearest city.
- Add `location_display` (string: "Region X, Province, City") to the incident response payload.
- On the frontend, render `location_display` wherever location is shown. If null, show "Location pending" instead of "N/A".

**Exit criteria:** An incident with a valid PostGIS point returns a non-N/A location string in both list and detail views.

---

### A3 · Search bar disappears after map pin drop
**Problem:** The fire scene location search bar disappears when the user drops a pin on the map manually.
**Fix:**
- Locate `MapPicker` or `MapPickerInner` component (likely in `src/frontend/src/components/`).
- Find the state variable that controls search bar visibility (likely toggled on `onLocationSelect` or similar callback).
- Remove the conditional that hides the search bar after a pin is placed. The search bar MUST remain visible and functional after manual pin placement so the user can correct the location via text search without refreshing.
- After a search result is selected, update the map pin position. After a manual pin drop, update the search bar's displayed value with the resolved address (reverse-geocoded from `wims.reference_cities`). Neither action should hide the other control.

**Exit criteria:** Drop a pin → search bar stays visible. Type a new location → pin moves. Both controls remain visible throughout the session.

---

### A4 · Add created_at / updated_at fields; sort dashboard by latest modified
**Problem:** No creation or modification timestamps are shown; dashboard list is not ordered by recency.
**Fix:**
- Confirm `fire_incidents` table has `created_at` and `updated_at` (TIMESTAMPTZ) columns. If `updated_at` lacks an auto-update trigger, add one:
  ```sql
  CREATE OR REPLACE FUNCTION wims.set_updated_at()
  RETURNS TRIGGER LANGUAGE plpgsql AS $$
  BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;
  CREATE TRIGGER trg_fire_incidents_updated_at
    BEFORE UPDATE ON wims.fire_incidents
    FOR EACH ROW EXECUTE FUNCTION wims.set_updated_at();
  ```
  Wrap in `IF NOT EXISTS` guards. Stop and ask before running on production.
- In `GET /api/regional/incidents`, add `created_at` and `updated_at` to the SELECT and to the response schema. Default ORDER BY: `updated_at DESC NULLS LAST, created_at DESC`.
- In the regional encoder dashboard (`src/frontend/src/app/dashboard/regional/`), add "Created" and "Last Modified" columns to the incident table. Format as PHT datetime. Ensure the list is sorted newest-first by `updated_at`.
- In the validator dashboard (`src/frontend/src/app/dashboard/validator/page.tsx`), apply the same `updated_at DESC` ordering.

**Exit criteria:** Incident list shows created/modified timestamps. Newest or most recently edited incident appears at the top of both dashboards.

---

## GROUP B — VALIDATOR FIXES

### B1 · Sort: newest submission at top of validator queue
**Problem:** The validator dashboard does not show the most recently submitted incidents at the top.
**Fix:**
- In `GET /api/regional/validator/incidents` (or `GET /api/validator/incidents`), change ORDER BY to `fi.created_at DESC` (submission time) as the primary sort.
- Expose `submitted_at` (alias for `created_at`) in the response payload.
- In the validator dashboard table, add "Time Submitted" as the leftmost column. Display in PHT format.

**Exit criteria:** Submit a new incident as encoder → it appears at the top of the validator queue immediately.

---

### B2 · Remove invalid action buttons on finalized incidents
**Problem:** "Return to Pending" and "Reject" buttons appear on already-VERIFIED incidents. "Return to Pending" and similar actions appear on already-REJECTED incidents.
**Fix:**
- In the validator dashboard (`page.tsx`) and the incident detail/action modal, conditionally render action buttons based on current `verification_status`:
  - Status = VERIFIED: show only "Archive" button. Hide Reject, Return to Pending, Accept.
  - Status = REJECTED: show only "Archive" button. Hide Accept, Return to Pending.
  - Status = PENDING or PENDING_REVIEW: show Accept, Reject, View Diff (if applicable).
- On the backend (`PATCH /api/regional/incidents/{id}/verification` or equivalent), the existing 409 idempotency guard already blocks invalid transitions — but also add explicit status guards to return 400 with a clear message for VERIFIED→REJECT or REJECTED→ACCEPT attempts.

**Exit criteria:** A VERIFIED incident shows only the Archive button. A REJECTED incident shows only the Archive button. No invalid transitions are possible from UI or API.

---

### B3 · Bulk Accept — preserve FIFO order; fix localhost popup
**Problem 1:** Bulk accept does not process incidents in submission order (oldest first).
**Problem 2:** The bulk accept confirmation popup references localhost instead of using the app's uniform modal UI.
**Fix:**
- In `POST /api/validator/incidents/bulk-approve` (or the equivalent bulk accept endpoint): before processing, sort `incident_ids` by `fi.created_at ASC` — oldest first — within the transaction. Do not rely on input order from the client.
- On the frontend, replace the `window.confirm("...localhost...")` call with the application's standard confirmation modal component (same modal style used for single-incident actions). The modal MUST show: the count of selected incidents, a Confirm button, and a Cancel button. No browser-native dialogs.

**Exit criteria:** Select 3 incidents in random order → bulk accept → they are approved oldest-first. Confirmation modal matches app UI, no localhost reference.

---

### B4 · Validator archive for VERIFIED and REJECTED incidents
**Problem:** Validators cannot archive finalized incidents. Replaced incidents have no designated storage with a "replaced" status.
**Fix:**
- Add `is_archived` (BOOLEAN DEFAULT FALSE) and `archived_at` (TIMESTAMPTZ) columns to `wims.fire_incidents` if not present. Wrap in `IF NOT EXISTS`. Stop and ask before executing on production.
- Add endpoint: `PATCH /api/validator/incidents/{id}/archive` — sets `is_archived = TRUE`, `archived_at = NOW()`. Only callable on VERIFIED or REJECTED incidents. Returns 400 if the incident is PENDING or DRAFT.
- The default query for `GET /api/validator/incidents` MUST filter `is_archived = FALSE`. Add an optional `?archived=true` query param to show the archive.
- On the frontend, add an "Archive" button (visible only on VERIFIED and REJECTED incidents). Add an "Archived" tab or filter toggle in the validator dashboard to browse archived incidents. Archived incidents are read-only — no further action buttons.
- Incidents that were replaced via duplicate resolution (see Group C) are auto-archived with `verification_status = 'REPLACED'`. Add REPLACED to the status enum and CheckConstraint. The archived view shows their status as "Replaced."

**Exit criteria:** Validator can archive a VERIFIED incident. Archived incidents disappear from the main queue. The archive tab shows them with correct status. A replaced incident appears in the archive as "Replaced."

---

## GROUP C — PRIORITY FIX: DUPLICATION DETECTION (complete rewrite)

This is the highest-priority group. Read all sub-items before making any changes. Implement atomically — do not partially implement.

### C0 · Core principle
Duplication detection triggers ONLY in these four scenarios. It must NOT trigger in any other case:
1. Encoder submits a DRAFT that is identical to one of their own PENDING or PENDING_REVIEW incidents.
2. Encoder submits a DRAFT that is identical to an already-VERIFIED incident.
3. Validator views or accepts an incident that is identical to another PENDING/PENDING_REVIEW or recently VERIFIED incident (consecutive/bulk accept scenario).
4. Two identical incidents are accepted consecutively or via bulk accept within a short time window.

Encoders MAY have multiple identical DRAFTS. DRAFT-to-DRAFT comparison MUST NOT trigger duplicate detection.

---

### C1 · Backend duplicate detection service
- Create or refactor `src/backend/services/duplicate_detection.py`.
- The detection function signature: `check_for_duplicate(db, incident_id, region_id, alarm_level, incident_date, lat, lon, exclude_statuses=['DRAFT', 'REPLACED', 'REJECTED'])`.
- Detection logic: query `wims.fire_incidents` joined to `wims.incident_nonsensitive_details` for incidents with the same `region_id`, `alarm_level`, and `incident_date`, within 1km (`ST_DWithin(fi.location, ST_SetSRID(ST_MakePoint(lon, lat), 4326), 0.009)`), with `verification_status NOT IN ('DRAFT', 'REPLACED', 'REJECTED')` and `is_archived = FALSE`.
- Return: `{is_duplicate: bool, matching_incident_id: uuid | None, matching_status: str | None}`.
- For scenario (d) — consecutive bulk accept — also query incidents verified within the last 60 seconds: add `AND fi.updated_at > NOW() - INTERVAL '60 seconds'` when checking against VERIFIED incidents in a bulk operation context.

---

### C2 · Encoder-side duplicate gate (submit draft → pending)
- In the endpoint that transitions an incident from DRAFT to PENDING/PENDING_REVIEW (likely `PUT /api/regional/incidents/{id}` with `submit=true` or a dedicated submit endpoint):
  - Call `check_for_duplicate(...)`.
  - If `is_duplicate = True`, do NOT submit. Return HTTP 409 with body: `{code: "DUPLICATE_DETECTED", matching_incident_id: "...", matching_status: "..."}`.
- On the frontend, intercept the 409 response and show a modal with the message:
  > "There's already an incident with the same details. What would you like to do?"
  - **Edit** — close modal, return to draft edit form.
  - **View existing** — open the matching incident in a new tab (read-only).
  - **Submit anyway** — re-call the submit endpoint with `?force=true` query param, which bypasses the duplicate check and submits as-is.
  - **Cancel** — close modal, stay on draft.
- The `?force=true` flag bypasses detection for this single submit. The `is_duplicate` field on the created incident is set to `FALSE` when forced.

---

### C3 · Validator-side duplicate handling
- When the validator opens or accepts an incident, call `check_for_duplicate(...)` server-side.
- If a duplicate is found, the side-by-side diff view is shown as a modal (existing component is acceptable — keep the current UI).
- The modal presents two action buttons:
  1. **Replace existing** — the duplicate incident inherits the reference number (`ref_number`) of the original. The original is soft-deleted and moved to the archive with `verification_status = 'REPLACED'`. The formerly-duplicate incident is set to VERIFIED. The `is_duplicate` flag on the now-verified incident is cleared to FALSE.
  2. **Accept as new** — verify the incident normally. Assign it a new reference number. Clear its `is_duplicate` flag to FALSE.
- After either action: the `is_duplicate` flag is FALSE, the side-by-side comparison NEVER appears again for this incident, and no "duplicate" badge is shown in the UI.

---

### C4 · Consecutive / bulk-accept duplicate guard
- In `POST /api/validator/incidents/bulk-approve`: after sorting by `created_at ASC`, iterate through each incident before approving it. For each, call `check_for_duplicate(...)` including the 60-second VERIFIED window.
- If a duplicate is detected mid-bulk: pause the batch for that incident. Return the batch result with `{approved: N, held_for_review: [{id, matching_incident_id}]}`.
- On the frontend, show the held incidents with a "Review duplicate" button. The validator resolves them individually before they are approved.
- For single consecutive accepts: apply the same 60-second VERIFIED check before approving each incident.

---

### C5 · Remove stale duplicate UI
- Find every place in the frontend where `is_duplicate` status badge or "duplicate" label is shown.
- Add the condition: only render the duplicate badge if `is_duplicate === true AND verification_status NOT IN ['VERIFIED', 'REJECTED', 'REPLACED']`.
- Never show the side-by-side comparison modal for incidents that are VERIFIED, REJECTED, or REPLACED — even if `is_duplicate` is somehow true in the DB. Add this guard both in the modal trigger and on the backend diff endpoint.

---

### C6 · Time input — 24-hour format (duplicate of A1 scoped here)
MUST be confirmed complete in Group A before this group is marked done. 24-hour HH:MM input is required for consistent duplicate matching on `incident_date` + time fields.

---

## GROUP D — AUDIT TRAIL

### D1 · Audit trail field standardization
The audit trail MUST capture and display these fields only:
- **Date & Time** — when the action occurred, in PHT (Asia/Manila), format: `YYYY-MM-DD HH:MM PHT`
- **Incident** — the incident reference number or ID
- **Region** — resolved region name using the format "Region I", "Region IV-A" (not raw region_id integers)
- **By** — the username (not UUID) of the actor

**Fix:**
- In `src/backend/` (audit log creation path — likely `utils/audit.py` or embedded in route handlers): ensure every audit write includes `incident_id`, `actor_user_id`, `region_id`, and `action_label`.
- Add `action_label` as a VARCHAR column to the audit log table if not present, with specific label values: `CREATED`, `EDITED`, `SUBMITTED`, `APPROVED`, `REJECTED`, `ACCEPTED_AS_NEW`, `REPLACED_EXISTING`, `BULK_APPROVED`, `ARCHIVED`, `EXPORTED_CSV`.
- In `GET /api/validator/audit-logs`, JOIN to `wims.users` on `actor_user_id` to return `username`. JOIN to `wims.regions` on `region_id` to return the formatted region name ("Region I", "Region IV-A"). Return `action_label` in the response.
- On the frontend audit trail page (`/dashboard/validator/audit`): update the table columns to: Date & Time | Incident | Region | By | Action. Remove any other columns.

---

### D2 · Fix audit CSV export (currently returns empty CSV)
- Locate the CSV export endpoint: `GET /api/validator/audit-logs/export?format=csv`.
- Debug: confirm whether the query returns zero rows (data issue) or whether the CSV serialization is broken (code issue). Add a debug log before the return.
- If the query is scoped incorrectly (e.g., filtering by a user_id that never matches), fix the WHERE clause.
- Ensure the CSV response has: `Content-Type: text/csv`, `Content-Disposition: attachment; filename="audit-log-{date}.csv"`, and correct column headers matching the D1 fields.
- Test: make at least one audit action, then export. The downloaded CSV MUST contain at least that row.

**Exit criteria:** Export CSV after performing any validator action → download contains non-empty rows with correct headers.

---

## GROUP E — POST-FIX VERIFICATION

After all groups A–D are complete, perform this verification pass. Output a checklist with ✅ or ❌ for each item.

```
ENCODING VERIFICATION
[ ] Time of notification: input 14:22 → stored as 06:22:00+00 → displayed as 14:22 PHT
[ ] Location: incident with valid PostGIS point → shows "Region X, Province, City" not "N/A"
[ ] Map search bar: visible before and after pin drop; updating search moves pin
[ ] Dashboard list: sorted by updated_at DESC; created_at and updated_at columns visible

VALIDATOR VERIFICATION
[ ] Validator queue: newest submission at top; "Time Submitted" column present leftmost
[ ] VERIFIED incident: only Archive button visible, no Reject/Return-to-Pending
[ ] REJECTED incident: only Archive button visible, no Accept/Return-to-Pending
[ ] Bulk accept: confirmation modal uses app UI (no localhost); incidents approved oldest-first
[ ] Archive: can archive VERIFIED or REJECTED incidents; archived tab shows them; DRAFT cannot be archived

DUPLICATE DETECTION VERIFICATION
[ ] Two identical DRAFTS: no duplicate warning triggered
[ ] DRAFT submitted as PENDING when identical PENDING exists: 409 modal shown with 4 options
[ ] DRAFT submitted as PENDING when identical VERIFIED exists: 409 modal shown with 4 options
[ ] Force submit: bypasses duplicate check, incident submitted without duplicate flag
[ ] Validator accepts a duplicate: side-by-side shown; Replace → original archived as REPLACED, ref_number inherited, duplicate flag cleared
[ ] Validator accepts a duplicate: Accept as new → new ref_number, duplicate flag cleared
[ ] After resolution: no duplicate badge, no side-by-side modal for that incident ever again
[ ] Consecutive accept of duplicate: 60-second window check triggers; held-for-review returned in bulk result
[ ] VERIFIED/REJECTED incidents: duplicate badge NEVER shown regardless of DB flag

AUDIT TRAIL VERIFICATION
[ ] Audit trail table shows: Date & Time | Incident | Region (formatted) | By (username) | Action
[ ] Action labels are specific: APPROVED, REPLACED_EXISTING, ACCEPTED_AS_NEW, etc.
[ ] Export CSV: non-empty, correct headers, correct data
```

---

## GROUP F — M4 MILESTONE GAP ANALYSIS

After verification, assess the current state of each M4 milestone item against `M4-INCIDENT-WORKFLOW-DETAILS.md`. For each item, output its status:

```
M4-A Incident Creation with PostGIS — ✅/⚠️/❌ [notes]
M4-B Incident Edit (Own, Non-Verified Only) — audit trail entry on edit: ✅/⚠️/❌
M4-C AFOR Spreadsheet Import — ✅/⚠️/❌
M4-D Duplicate Detection on Import — ✅/⚠️/❌ [now covered by Group C]
M4-E Draft Save — auto-expiry Celery task: ✅/⚠️/❌
M4-F Validator Queue — cross-region queue; audit per action: ✅/⚠️/❌
M4-G Side-by-Side Diff View — ✅/⚠️/❌ [now gated by Group C rules]
M4-H Bulk Approve — all exit criteria: ✅/⚠️/❌
M4-I Audit Trail Viewer — all filters and CSV export: ✅/⚠️/❌
```

For every item marked ⚠️ or ❌ where the current system files do not already contain an implementation path, produce a concise **Implementation Plan** using this template:

```
### Gap Plan: [M4-X title]
Objective: [one sentence]
Files to modify: [list]
Files to create: [list]
Steps:
1. [specific step with exact route path / function name / column name]
2. ...
Exit criteria: [maps to the unchecked [ ] items in M4-INCIDENT-WORKFLOW-DETAILS.md]
Do not touch: [list files outside scope]
```

Only produce Gap Plans for items not already addressed in Groups A–D above. Do not re-plan what was already fixed.
```

---

🎯 **Target:** Claude Code
💡 **Optimized for:** Agentic multi-group execution with explicit scope locks, stop-and-ask guards on destructive operations, and per-group exit criteria — prevents partial states and scope creep across a complex bug-fix + feature-gap session.

> **Before pasting:** Open the repo root in Claude Code. Attach `M4-INCIDENT-WORKFLOW-DETAILS.md` as context if your session supports file attachment. Execute Group A first, verify its exit criteria, then proceed to B → C → D → E → F in order.
