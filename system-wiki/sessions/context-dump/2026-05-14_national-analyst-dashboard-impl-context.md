# Context Dump — National Analyst Dashboard Implementation
**File:** `2026-05-14_XXXX_national-analyst-dashboard-impl-context.md`
**Author:** Ares (Principal Systems Architect)
**Date:** 2026-05-14
**Purpose:** Full scope context for a specialized sub-agent to execute implementation

---

## What We Did in the Grill-Me Session

We went through a decision-tree walk of the National Analyst Dashboard implementation scope. Every branch was resolved and confirmed with the user. This document is the authoritative output of that session.

---

## Confirmed Implementation Scope (6 Phases)

### Phase 1 — Export Infrastructure Fix (backend)

**Problem:** `src/backend/tasks/exports.py` is broken:
- `export_incidents_pdf_task` (line 122): writes HTML to `.html` file. `reportlab` not in `requirements.txt`.
- `export_incidents_excel_task` (line 167): writes CSV to `.csv` file using Python's csv writer (not openpyxl). `openpyxl` IS in requirements but task doesn't use it.
- No `GET /api/analytics/export/{task_id}` download endpoint found in `analytics.py`.
- `analytics_export_log` INSERT not found in task code — audit trail may not be wired.

**Fix required:**
1. Add `reportlab>=4.0` to `src/backend/requirements.txt`
2. Rewrite `export_incidents_pdf_task` to produce actual PDF using reportlab `Table`/`Paragraph`
3. Rewrite `export_incidents_excel_task` to use openpyxl `Workbook`
4. Add `GET /api/analytics/export/{task_id}` download endpoint to `src/backend/api/routes/analytics.py`
5. Wire `analytics_export_log` INSERT in all three export tasks (PDF, Excel, CSV)

**Key files:**
- `src/backend/tasks/exports.py` — the broken tasks
- `src/backend/api/routes/analytics.py` — where to add download endpoint
- `src/backend/requirements.txt` — add reportlab

---

### Phase 2 — Analytics Schema Migration (backend)

**Decision:** Denormalized for analytics. Normalized reference tables are for transaction-heavy tables.

**New migration file:** `src/postgres-init/XX_analytics_geography_denorm.sql` (auto-assign number)

**Changes:**
1. `ALTER TABLE wims.analytics_incident_facts ADD COLUMN IF NOT EXISTS municipality_name TEXT`
2. `ALTER TABLE wims.analytics_incident_facts ADD COLUMN IF NOT EXISTS province_name TEXT`
3. Update `sync_incident_to_analytics` in `src/backend/services/analytics_read_model.py`:
   - SELECT: add `nd.province_district` and `nd.city_municipality` from the JOIN with `incident_nonsensitive_details nd`
   - UPSERT: include both in the INSERT/ON CONFLICT DO UPDATE SET

**Source columns (from `incident_nonsensitive_details`):**
- `nd.city_municipality` → `municipality_name`
- `nd.province_district` → `province_name`

**No `ref_municipalities` table** — denormalized free text in analytics facts table. This is intentional per user decision.

**Dependency:** Phase 1 is independent of Phase 2. Can run in parallel or after.

---

### Phase 3 — Filter Options API (backend)

**New endpoint:** `GET /api/analytics/filter-options`

**Query params:**
- `field` — required, one of: `municipality`, `province`

**Behavior:**
- Returns distinct values from `analytics_incident_facts` for the requested field
- Optionally scoped by active filters (region_id, date range) — use same filter pattern as existing analytics endpoints
- Returns JSON array of strings: `["City A", "City B", ...]`

**Files:**
- `src/backend/api/routes/analytics.py` — add new route
- `src/backend/services/analytics_read_model.py` — add `get_filter_options(db, field)` function

---

### Phase 4 — National Analyst Dashboard Enhancements (frontend)

**Recharts installation:**
- Run: `cd src/frontend && npm install recharts`
- Update `package.json` to include `recharts`

**New filter fields (in filter bar):**
- `Municipality` dropdown — populated by `GET /api/analytics/filter-options?field=municipality`
- `Province` dropdown — populated by `GET /api/analytics/filter-options?field=province`
- Cascading behavior: Region selected → Province dropdown shows only provinces in that region; Province selected → Municipality dropdown shows only municipalities in that province
- If no Region selected: Province dropdown shows all provinces nationwide
- If no Province selected: Municipality dropdown shows all municipalities
- No reverse auto-selection (cleaner UX)

**Chart upgrades (replace text lists with Recharts):**

| Section | Chart Type | Recharts Component |
|---|---|---|
| AQ-06: Type Distribution | Pie or donut chart | `<PieChart>` with `<Cell>` |
| AQ-07: Top Barangays | Horizontal bar chart | `<BarChart>` with `layout="vertical"` |
| AQ-08: Response Time by Region | Bar chart (avg + min/max optional) | `<BarChart>` |

All three charts respond to the full filter bar (date range, region, incident type, alarm level, casualty severity, damage range, municipality, province).

**Existing components:**
- `src/frontend/src/app/dashboard/analyst/page.tsx` — main page (read it before editing)
- `src/frontend/src/components/analytics/TrendCharts.tsx` — existing chart component reference for style
- `src/frontend/src/lib/api.ts` — API functions

**Key confirmed findings from direct read:**
- Recharts was NOT in `package.json` (confirmed absent)
- AQ-06/07/08 were rendered as `flex` list-rows with `data-testid="pie-chart"` and `data-testid="bar-chart"` — these are mislabeled, no Recharts involved
- All three need full replacement with Recharts components

---

### Phase 5 — Incident List Container (frontend)

**Purpose:** Dedicated incident list/table that responds to the filter bar (fixes L-03 from gap register: "no dedicated incident container/list panel")

**Format:** Paginated table, 25 rows per page.

**Columns:**
1. `notification_dt` — date/time
2. `region` — short name via `getShortRegionName()`
3. `municipality_name`
4. `barangay_name`
5. `general_category` — AFOR: Structural/Non-Structural/Transportation; Wildland: Brush/Forest/Grassland/etc.
6. `sub_category` — specific type within general_category (e.g., Apartment Building, Brush Fire, etc.)
7. `alarm_level`
8. `estimated_damage_php`
9. `total_response_time_minutes`

**No verification_status column** — analyst only sees VERIFIED incidents.

**Data source:** Backend endpoint `GET /api/incidents/list` (new — see below). Not from analytics_incident_facts (no schema change needed; sub_category already exists in incident_nonsensitive_details).

**Backend endpoint for incident list:**
- `GET /api/incidents/list` in `src/backend/api/routes/incidents.py`
- Query params: `start_date`, `end_date`, `region_id`, `incident_type`, `alarm_level`, `casualty_severity`, `damage_min`, `damage_max`, `municipality`, `province`, `page`, `page_size=25`
- WHERE clause filters: `verification_status = 'VERIFIED'` always (analyst scope)
- Returns: `{ incidents: [...], total: N, page: N, page_size: 25 }`

**Interaction:** Click row → side drawer opens.
- Side drawer shows: incident summary (key fields)
- Side drawer has "Open Full Page" button → navigates to `/dashboard/analyst/incidents/[id]`

**Location in `analyst/page.tsx`:** Place below the charts grid, separated by a section header "Incident List".

---

### Phase 6 — Analyst Incident Detail Page (frontend)

**Route:** `src/frontend/src/app/dashboard/analyst/incidents/[id]/page.tsx` (new file)

**Purpose:** Read-only incident detail page for national analysts. No edit mode, no validator actions.

**Display:** All AFOR sections A–L, same structure as the existing `src/frontend/src/app/dashboard/regional/incidents/[id]/page.tsx`.

**Key difference from regional_encoder page:** No edit button, no validator accept/reject actions, no AFOR form (IncidentForm). Pure read-only display.

**Sections to display:**
- Section A: Fire Notification Details (notification_dt, alarm_level, responder_type, etc.)
- Section B: Classification (general_category, sub_category, specific_type, occupancy_type)
- Section C: Location (barangay, municipality, province, distance_from_station, latitude/longitude with map)
- Section D: Incident Timeline (alarm_timeline)
- Section E: Casualties
- Section F: Personnel on Duty
- Section G: Incident Command Post
- Section H: Fire Scene Location (map)
- Section H-alt: Sketch attachment if present
- Section I: Narrative Report
- Section J: Problems Encountered
- Section K: Recommendations
- Section L: Disposition & Signatories

**Also display:**
- Chain of custody provenance (from M6-D): `data_hash`, `created_at`, `encoder_id`
- Analytics sync status (if applicable)

**Export buttons:** Export PDF + Export CSV (call the fixed export infrastructure from Phase 1).

**Access control:** `NATIONAL_ANALYST` and `SYSTEM_ADMIN` only.

---

## Confirmed Findings from Codebase Read (Ground Truth)

### Export Infrastructure
- `reportlab` not in `requirements.txt` — needs to be added
- `openpyxl` IS in requirements.txt but not used by `export_incidents_excel_task`
- No download endpoint in `analytics.py`

### Schema
- `analytics_incident_facts` base: 5 columns (incident_id, region_id, location, notification_dt, notification_date, alarm_level, general_category, synced_at)
- Richer schema comes from `12_analytics_mvs.sql` ALTER TABLE expansions: civilian_injured, civilian_deaths, firefighter_injured, firefighter_deaths, total_response_time_minutes, estimated_damage_php, fire_station_name, barangay_name
- `municipality_name` and `province_name` are NOT yet in `analytics_incident_facts` — this is the Phase 2 migration
- `sub_category` in `incident_nonsensitive_details` is plain VARCHAR — no DB-level CHECK constraint, enforced by frontend dropdown only

### Recharts
- Not in `package.json` — confirmed absent
- `TrendCharts.tsx` and `HeatmapViewer.tsx` exist as components

### Incident Detail Pages (existing)
- `src/frontend/src/app/dashboard/regional/incidents/[id]/page.tsx` — full read/edit page (1265 lines), AFOR sections A–L, edit button, validator actions, no export
- `src/frontend/src/app/incidents/[id]/page.tsx` — redirector (35 lines), redirects to regional

### Top-N
- `VALID_TOP_N_DIMENSIONS` in `analytics_read_model.py`: barangay, fire_station, region
- `municipality` NOT in the list — G-01 confirmed

---

## Thesis-Wiki Recommendation (Phase 7 — documentation only)

**Recommendation:** Add DB-level CHECK constraints on `general_category` and `sub_category` in `incident_nonsensitive_details` as defense-in-depth against curl/Postman bypass of frontend dropdowns.

**Rationale:** Frontend dropdowns enforce valid values, but a threat actor with knowledge of the API could POST arbitrary strings via curl. CHECK constraints provide a second layer.

**Do NOT implement in this sprint** — document as a recommendation in the thesis-wiki under security hardening section. Implementation is out of scope for the current phase.

---

## Do Not Break Conventions

- `regional.py` is monolithic — do not split it
- `get_db` vs `get_db_with_rls` are different dependency tokens — overriding one does not affect the other
- `KeycloakOpenIDConnection(username/password)` is broken in python-keycloak 7.1.1 — use `KeycloakOpenID.token()` + `KeycloakAdmin(token=)` instead
- Anonymous submissions: `encoder_id = NULL`, `verification_status = PENDING_VALIDATION`
- Wiki `raw/` directory is immutable — update synthesis pages, not raw sources

---

## Key File Locations

| Artifact | Path |
|---|---|
| Export tasks (broken) | `src/backend/tasks/exports.py` |
| Analytics routes | `src/backend/api/routes/analytics.py` |
| Analytics read model | `src/backend/services/analytics_read_model.py` |
| Backend requirements | `src/backend/requirements.txt` |
| Postgres migrations | `src/postgres-init/` |
| Analyst page | `src/frontend/src/app/dashboard/analyst/page.tsx` |
| Regional incident detail (reference) | `src/frontend/src/app/dashboard/regional/incidents/[id]/page.tsx` |
| Frontend API lib | `src/frontend/src/lib/api.ts` |
| Package.json | `src/frontend/package.json` |
| System wiki | `system-wiki/` |

---

## Dependency Order

```
Phase 1 (Export fix)      ─┐
                           ├─► Phase 5 (Incident list container)
Phase 2 (Schema migrate)  ─┤        │
                           │        ▼
Phase 3 (Filter options) ─┴──► Phase 4 (Charts + filters)
                                    │
                                    ▼
                              Phase 6 (Analyst detail page)
```

Phase 1 and Phase 2 can run in parallel.
Phase 3 depends on Phase 2 (province/municipality columns must exist before filter-options can query them).
Phase 4 depends on Phase 3 (filters need the endpoint before they can populate).
Phase 5 (incident list) depends on Phase 1 (export) for the download buttons — but the list itself can be built once export endpoint exists.
Phase 6 (analyst detail page) depends on Phase 1 for export buttons and Phase 2 for any analytics data displayed.

**Minimum viable order:**
1. Phase 1 (export fix) — unblocks Phase 5 and Phase 6 export buttons
2. Phase 2 (schema migration) — unblocks Phase 3
3. Phase 3 (filter options API) — unblocks Phase 4 municipality/province dropdowns
4. Phase 4 (charts + filters) — frontend work
5. Phase 5 (incident list container) — frontend work
6. Phase 6 (analyst detail page) — frontend work