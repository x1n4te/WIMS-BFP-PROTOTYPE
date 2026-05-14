# fix(afor): form cleanup, audit trail, and validator role fixes

## Summary

- XLSX import now writes `CREATED_DRAFT` audit log entries (was only logged on manual create)
- `VALIDATOR` role now has full validator access in the backend (was missing from `is_validator` check, causing 404s)
- `extent_description` and `extent_objects_count` added to `upload-bundle` INSERT (columns existed in DB via migration 25 but were never persisted for manually-created incidents)
- Stage of Fire dropdown options capitalized consistently
- Removed redundant Extended Beyond sub-fields from AFOR form (Structures/Objects/Vehicles already captured in Number Affected section)
- Removed Remarks column from Other Personnel at the Scene section
- Activity Log moved from Regional Dashboard header to sidebar nav
- Add New Incident button added to Regional Dashboard
- Back buttons styled consistently (bordered pill) across audit/import/create pages
- Removed wildland hint text from manual entry page

## Changed Files

| File | Change |
|------|--------|
| `src/backend/api/routes/regional.py` | Add `"VALIDATOR"` to `is_validator` check; add `CREATED_DRAFT` audit log in XLSX commit loop |
| `src/backend/api/routes/incidents.py` | Add `extent_description`, `extent_objects_count` to `upload-bundle` nonsensitive INSERT |
| `src/postgres-init/25_extent_fields.sql` | New migration — `extent_description TEXT`, `extent_objects_count INT` on `incident_nonsensitive_details` |
| `src/frontend/src/components/IncidentForm.tsx` | Capitalize Stage of Fire options; remove Extended Beyond sub-fields; remove Remarks from Other Personnel; update hydration/auto-fill accordingly |
| `src/frontend/src/components/Sidebar.tsx` | Add Activity Log to REGIONAL_ENCODER sidebar nav |
| `src/frontend/src/app/dashboard/regional/page.tsx` | Replace Activity Log link with Add New Incident button |
| `src/frontend/src/app/dashboard/regional/audit/page.tsx` | Bordered back button style |
| `src/frontend/src/app/dashboard/validator/audit/page.tsx` | Bordered back button style |
| `src/frontend/src/app/afor/create/page.tsx` | Remove wildland hint text; bordered back button style |
| `src/frontend/src/app/dashboard/regional/incidents/[id]/page.tsx` | View page fixes |
| `src/frontend/src/lib/afor-utils.ts` | `displayValue` returns N/A for 0 / "0" |

## Bug Fixes Detail

### VALIDATOR role — 404 on incident detail
`regional.py` `is_validator` only included `NATIONAL_VALIDATOR`, `SYSTEM_ADMIN`, `NATIONAL_ANALYST`. Users with the `VALIDATOR` role were routed through the encoder branch, which filters by `encoder_id`, returning 404 for any incident they didn't personally create.

**Fix:** Added `"VALIDATOR"` to the tuple.

### extent_description / extent_objects_count never saved (manual entry)
Migration 25 added these two columns but the `upload-bundle` INSERT in `incidents.py` didn't include them. Values entered in the form were silently dropped.

**Fix:** Added both columns + bound params to the INSERT.

### XLSX import missing CREATED_DRAFT audit entry
The manual create path (`POST /incidents`) logged `CREATED_DRAFT` but the XLSX commit loop (`POST /regional/afor/commit`) did not. Encoder activity log was missing all import-originated incidents.

**Fix:** Added `_insert_incident_verification_history()` call inside the per-row commit loop with `action_label="CREATED_DRAFT"`.

## Test Checklist

- [ ] Log in as `encoder_test`, import an XLSX — verify Activity Log shows `Created Draft` entries
- [ ] Log in as `validator_test` (VALIDATOR role), open any incident — verify it loads (no 404)
- [ ] Create a manual AFOR, select an Extent of Damage, fill sub-fields — save and verify `extent_description` appears in incident detail view
- [ ] Verify Stage of Fire dropdown shows: Incipient / Growth / Fully Developed / Decay
- [ ] Verify Other Personnel section has two columns (Name + Designation) — no Remarks input
- [ ] Verify Extended Beyond Structure does not show extra sub-fields below the radio
- [ ] Verify Activity Log appears in sidebar for encoder; Regional Dashboard shows Add New Incident button
- [ ] Build: `cd src && docker-compose up -d --build backend frontend`

## Migration Note

`25_extent_fields.sql` runs automatically on a fresh container start. If the Postgres container is already running with existing data, apply manually:

```sql
ALTER TABLE wims.incident_nonsensitive_details
  ADD COLUMN IF NOT EXISTS extent_description TEXT,
  ADD COLUMN IF NOT EXISTS extent_objects_count INT;
```
