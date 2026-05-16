# Handoff: TOP-N Barangay Dimension Fix

**Date:** 2026-05-16
**User:** x1n4te
**Session:** TOP-N barangay gap identified → OpenCode subagent → code resolved → system-wiki updated

---

## What happened

### Gap identified
TOP-N by barangay dimension was returning empty results for all AFOR-imported and manual-create incidents. Root cause traced through the full stack:

1. `ref_barangays` has no geometry column — no spatial lookup possible
2. AFOR import (`parse_afor_report_data`) only resolves `city_id` from text; `barangay_id` is never written to `incident_nonsensitive_details`
3. Manual create (`IncidentCreateRequest`) accepts `barangay_id` as optional; the INSERT also doesn't write it
4. `sync_incident_to_analytics` pulls `barangay_name` via `LEFT JOIN ref_barangays ON bararangay_id = nd.barangay_id` — returns NULL when `nd.barangay_id` is NULL
5. `get_top_n` filters `WHERE {dim_col} IS NOT NULL` — returns empty for barangay

### Fix implemented (via OpenCode subagent, commit `4fb24b7`)

**1. Migration — `src/postgres-init/31_barangay_geometry.sql`**
- Adds `geometry GEOGRAPHY(POLYGON, 4326)` to `ref_barangays`
- Creates `idx_ref_barangays_geometry` GiST index
- Idempotent (`ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`)
- Note: PSGC barangay polygon SHP data must be loaded separately

**2. Function — `_reverse_geocode_barangay(db, incident_id, lon, lat)` in `src/backend/api/routes/regional.py`**
- Checks if any `ref_barangays` row has non-NULL geometry before querying (graceful degradation — logs warning and skips if not yet loaded)
- Uses `ST_Contains(rb.geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)` to find containing barangay
- `UPDATE incident_nonsensitive_details SET barangay_id = :bid WHERE incident_id = :iid`
- Calls `sync_incident_to_analytics(db, incident_id)` to refresh analytics facts

**3. Call sites (3 locations in `regional.py`)**
- `_commit_wildland_afor_row` (line 1533) — after wildland fire_incident INSERT
- AFOR structural commit loop (line 1960) — after structural incident INSERT
- `create_incident` (line 3165) — after manual create INSERT, before `db.commit()`

### System wiki updated
- `system-wiki/gaps/frs-codebase-gap-register.md` — gap marked **RESOLVED in code, verification pending**
- `system-wiki/log.md` — fix logged (entries reordered to reverse-chronological)

---

## What's still needed

### Verification pending (blocking)
1. **Load PSGC barangay polygon SHP data** into `ref_barangays.geometry` — without this, `_reverse_geocode_barangay` logs a warning and skips, so `barangay_name` stays NULL for all incidents
2. **Re-sync existing incidents** — after polygon data is loaded, run `sync_incident_to_analytics` for all VERIFIED incidents that have a location but NULL `barangay_id`

### How to verify the fix works end-to-end
1. Load PSGC shapefiles into `ref_barangays.geometry` for a known city/municipality
2. Create a test incident with coordinates that fall inside one of the loaded barangay polygons
3. Call `GET /api/regional/incidents` or check `incident_nonsensitive_details` directly — `barangay_id` should be populated
4. Call `GET /api/analytics/top-n?dimension=barangay&metric=incidents` — should return ranked barangays, not empty

---

## Affected files
- `src/postgres-init/31_barangay_geometry.sql` — **created**
- `src/backend/api/routes/regional.py` — **modified** (+71 lines: `_reverse_geocode_barangay` function + 3 call sites)
- `system-wiki/gaps/frs-codebase-gap-register.md` — **updated**
- `system-wiki/log.md` — **updated**

---

## Branch
`feature/national-analyst-dashboard` — commit `4fb24b7 feat(geography): reverse-geocode barangay_id after incident insert`

---

## Suggested next session focus
1. Load PSGC barangay polygon data (one city as proof-of-concept)
2. Verify end-to-end: create incident → check `barangay_id` populated → TOP-N by barangay returns results
3. Write a backfill script for existing VERIFIED incidents that have `location` but NULL `barangay_id`

## Skills to use
- `wims-bfp` — for understanding WIMS-BFP data model conventions
- `improve-codebase-architecture` — if designing the backfill script