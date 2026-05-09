# M4 Incident Workflow — Implementation Status Update

## Summary

- Closes M4-A (Incident Creation), M4-C (AFOR Import), M4-F (Validator Queue), M4-G (Diff View), M4-H (Bulk Approve), M4-I (Audit Trail) — all fully implemented
- M4-B (Incident Edit) and M4-E (Draft Save) are partial — ownership enforcement and Celery expiry still pending
- Three systems added beyond the original M4 spec: duplicate detection (encoder + validator sides), incident archive / REPLACED status, and AFOR reference number generation

---

## What's Implemented

### Duplicate Detection System (new — beyond spec)

- **Encoder submits** → backend spatial check (5 km `ST_DWithin` + optional ±1 day date window) → 409 if match found → encoder modal: Submit Anyway / View Existing / Edit / Cancel
- **Validator clicks Accept** → same check fires immediately (no intermediate Confirm step) → if 409, side-by-side comparison modal opens automatically with: Replace Existing / Verify as New / Reject / Cancel
- `services/duplicate_detection.py` — dedicated service used by 4 call sites (submit, verify, bulk-approve, ack_duplicate)
- Date filter is skipped when `notification_dt` is absent (spatial-only fallback); update requests are excluded from the validator-side check to prevent false positives

### Archive & REPLACED Status (new — beyond spec)

- `PATCH /api/regional/validator/incidents/{id}/archive` — archives VERIFIED / REJECTED / REPLACED incidents
- `archived_at TIMESTAMPTZ` column; `verification_status` CHECK expanded to include `REPLACED`
- `action_label VARCHAR(80)` added to `incident_verification_history`
- Archived tab in validator queue (`?archived=true`)

### Validator Queue Enhancements (M4-F)

- Direct Accept flow — clicking Accept immediately calls the backend; 409 opens side-by-side modal automatically
- Conditional action buttons — finalized incidents (VERIFIED / REJECTED / REPLACED) show Archive only
- Bulk confirm in-app modal (replaces `window.confirm`)
- Chronological bulk processing (oldest first) + mid-batch duplicates returned as `held_for_review`

### Side-by-Side Diff View (M4-G)

- `UpdateRequestDiffPanel` component for update requests
- Duplicate resolution modal for validator with 4 options: Replace Existing / Verify as New / Reject / Cancel
- Auto-show on incident detail page when `is_duplicate = TRUE` and `duplicate_of` is set

### Audit Trail (M4-I)

- `actor_username` and `region_display` resolved (not raw UUID / region_id)
- `action_label` per action — human-readable labels
- CSV export with date-stamped filename
- Columns: Date & Time | Incident | Region | By | Action

---

## Remaining Gaps (Not in This PR)

| Gap | Location | Fix |
|-----|----------|-----|
| Backend encoder ownership guard on edit | `update_incident()` | Add `AND encoder_id = :uid` to UPDATE + 403 on rowcount=0 |
| Edit creates audit trail entry | `update_incident()` | INSERT into `incident_verification_history` with `action_label='EDITED'` |
| Celery draft auto-expiry (30 days) | `tasks/draft_expiry.py` (new) | Celery periodic task, beat schedule entry |
| AFOR import per-row duplicate decision UI | `/afor/import` | Review modal with Skip / Merge / Force per row before commit |

---

## Test Plan

- [ ] Submit a new incident at the same station/location as an existing VERIFIED incident → encoder sees 409 duplicate modal with 4 options
- [ ] Force-submit through → PENDING incident created
- [ ] Validator clicks **Accept** → side-by-side comparison modal appears immediately showing PENDING vs VERIFIED incident
- [ ] Click **Replace Existing** → new incident VERIFIED with original ref number; old marked REPLACED + archived
- [ ] Click **Verify as New** → new incident VERIFIED with new ref number; old unaffected
- [ ] Click **Reject** → incident rejected, notes required
- [ ] Click **Cancel** → incident stays PENDING
- [ ] Archive a VERIFIED incident → moves to Archived tab; no action buttons shown
- [ ] Bulk approve: select PENDING incidents → in-app confirm modal → chronological processing
- [ ] Audit trail: Date/Time, Incident, Region (name), By (username), Action (label) all populated
- [ ] CSV export → non-empty, correct headers, date-stamped filename

---

🤖 Generated with [Claude Code](https://claude.ai/claude-code)
