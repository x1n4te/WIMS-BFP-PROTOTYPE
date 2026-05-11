# M4 Incident Workflow — Complete Implementation

## Summary

- Completes M4-A through M4-I (M4-D per-row UI deferred by design)
- Adds 5 systems beyond original spec: encoder audit trail, duplicate detection, archive/REPLACED status, AFOR reference numbers, regional RBAC
- Fixes 7 system-test bugs: reference number format, required field validation, region enforcement, classification labels, region display names, and validator refresh notification

---

## What's New

### Encoder Audit Trail (new — beyond spec)

- `GET /api/regional/audit-log` — encoder's own action history, paginated with date range filter
- `POST /incidents` now writes `action_label='CREATED_DRAFT'` on creation
- Draft edit writes `EDITED`; draft delete writes `DELETED_DRAFT`; submit writes `SUBMITTED`
- Frontend: `/dashboard/regional/audit` — "My Activity Log" page
- Activity Log link added to regional dashboard nav

### Regional RBAC (new — beyond spec)

- 18 Keycloak encoder accounts (`encoder_r01` – `encoder_r18`), one per PH region
- `encoder_test` remains Region 1 (NCR) for development use
- `seed-dev-users.sh` and `.ps1` updated with all 18 encoders and their region assignments
- Backend `POST /incidents` and `POST /incidents/upload-bundle` enforce `region_id == assigned_region_id` (HTTP 403 REGION_MISMATCH)
- Frontend: 403 from backend shows a clean inline message with the region field highlighted in red; no raw error codes shown

### Reference Numbers (new — beyond spec)

Format: `AFOR-RGN-{REGION}-{STATION}-{TYPE}-{MON}-{YEAR}-{SEQ:04d}`

Region codes use Arabic numerals: RGN-NCR, RGN-CAR, RGN-NIR, RGN-BARMM, RGN-1 through RGN-13

Sequence is **global** — monotonically incrementing across all incidents.

Reference number preview in the encoder form now matches the backend format (Arabic numerals, not Roman).

### Duplicate Detection System (new — beyond spec)

- `services/duplicate_detection.py` — spatial + temporal check (5 km `ST_DWithin` + ±1 day date window)
- Encoder submit → 409 DUPLICATE_DETECTED → modal: Submit Anyway / View Existing / Edit / Cancel
- Validator accept → same check; on 409, side-by-side modal opens automatically with: Replace Existing / Verify as New / Reject / Cancel
- Replace Existing: new incident VERIFIED with original's reference number; old marked `REPLACED` + archived

### Archive & REPLACED Status (new — beyond spec)

- `PATCH /api/regional/validator/incidents/{id}/archive` — archives VERIFIED / REJECTED / REPLACED incidents
- `archived_at TIMESTAMPTZ` column; `REPLACED` added to status CHECK constraint
- Archived tab in validator queue (`?archived=true`)

### Validator Queue Enhancements (M4-F)

- Direct Accept flow — clicking Accept immediately calls the backend; 409 opens side-by-side modal automatically
- Conditional action buttons — finalized incidents show Archive only; pending show Accept + Reject
- Bulk confirm in-app modal (replaces `window.confirm`)
- Newest-first sort; Submitted column showing `created_at` in PHT
- **Refresh notification** — background poll every 30 s; blue banner "New incidents have been submitted — Refresh now" when count increases

### Side-by-Side Diff View (M4-G)

- `UpdateRequestDiffPanel` for update requests
- Duplicate resolution modal: Replace Existing / Verify as New / Reject / Cancel
- Auto-show on incident detail page when `is_duplicate = TRUE`

### Validator Audit Trail (M4-I)

- `action` filter: APPROVED / REJECTED / BULK_APPROVED / REPLACED_EXISTING / ACCEPTED_AS_NEW / ARCHIVED
- `actor_username` and `region_display` resolved (not raw UUID / region_id)
- CSV export with date-stamped filename

### Required Field Validation (M4-A / M4-B)

- Frontend form: Province/District, City/Municipality, Prepared by, Noted by required
- Detail page submit button: checks all required fields from live `detail` data; shows modal listing missing fields
- Backend submit endpoint: HTTP 422 if `province_district` or `city_municipality` is NULL

### Draft Save & Auto-Expiry (M4-E)

- Celery `expire-stale-drafts-daily` task — expires DRAFT incidents older than 30 days
- Beat schedule entry in `celery_config.py`

---

## Bug Fixes

| Bug | Fix |
|-----|-----|
| Prepared by / Noted by false validation | Detail page now checks both `prepared_by_officer` AND `disposition_prepared_by` columns |
| Region enforcement bypass via auto-fill | `resolveRegionId()` always returns `assignedRegionId` for encoders; upload-bundle enforces on backend |
| Province/District + City/Municipality not required | Added to frontend validation + backend submit gate (422) |
| Long region names in dashboard | `getShortRegionName(regionId)` used in validator page, incident detail, analyst page |
| Classification labels had "Fire" suffix | `CLASSIFICATION_LABELS` now: Structural, Non-Structural, Transportation, Wildland |
| VEHICULAR vs TRANSPORTATION inconsistency | Both values handled in `getTypeOptionsForClassification`; form uses TRANSPORTATION by default |
| Validator refresh notification missing | 30-second background poll + blue banner when incident count increases |

---

## Remaining Gaps (Not in This PR)

| Gap | Notes |
|-----|-------|
| M4-D: AFOR import per-row duplicate decision UI | Duplicates are detected and counted; per-row skip/merge/force UI is deferred |
| Bulk approve atomicity | Mid-batch failure leaves earlier incidents approved — no rollback |

---

## Test Plan

- [ ] Create incident as `encoder_r04` (Region IV-A) — region dropdown locked to assigned region
- [ ] Submit incident → 409 duplicate modal with 4 options
- [ ] Force-submit → PENDING; validator clicks Accept → side-by-side modal opens automatically
- [ ] Click Replace Existing → new VERIFIED with original ref number; old marked REPLACED + archived
- [ ] Click Verify as New → new VERIFIED with new ref number; original unaffected
- [ ] Click Reject → notes required; incident REJECTED
- [ ] Archive a VERIFIED incident → moves to Archived tab; no action buttons
- [ ] Bulk approve: select PENDING incidents → in-app confirm → chronological processing
- [ ] Validator audit trail: filter by action=REJECTED → only rejected rows; CSV export non-empty
- [ ] Encoder audit log: CREATED_DRAFT, SUBMITTED, EDITED, DELETED_DRAFT entries visible
- [ ] Submit without Province/District → frontend highlight + detail-page modal lists it; backend returns 422
- [ ] Reference number on verified incident: format `AFOR-RGN-NCR-TBA-APT-MAY-2026-XXXX` with Arabic numeral region
- [ ] Validator refresh banner appears after 30 s when a new incident is submitted
- [ ] Try submitting from wrong region via upload-bundle → 403; clean error message, region field highlighted

---

🤖 Generated with [Claude Code](https://claude.ai/claude-code)
