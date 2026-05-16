# National Analyst Dashboard Implementation Plan

## Summary

Implement the National Analyst Dashboard work as a staged feature set grounded in the
system-wiki handoff/context dump plus the live code state. The plan keeps the six locked
phases, adds the missing wiki-evaluation items that affect completion, and treats
NATIONAL_ANALYST/SYSTEM_ADMIN access as fail-closed throughout.

Key decisions locked:

- Detail exports: full AFOR PDF/CSV, not summary-only.
- Incident list: 25 rows/page, default notification_dt DESC, sortable headers, wide
drawer.
- Wildland: separate analyst wildland detail route/layout when wildland AFOR data
exists.
- Geography: denormalized municipality_name and province_name on
analytics_incident_facts.
- Raw wiki sources stay immutable; update synthesis pages, gap registers, and system-
wiki/log.md.

## Implementation Changes

### 0. Preflight And Sync Verification

- Verify Issue #84 remains fixed: verify_incident() calls sync_incident_to_analytics()
after VERIFIED transitions and replacement archival paths.
- Add or keep regression coverage that proves verified incidents are inserted into
analytics facts and unverified/archived incidents are removed.
- Do not rework regional.py structure; only touch the existing verification sync
behavior if a regression is found.

### 1. Export Infrastructure

- Add reportlab>=4.0 to src/backend/requirements.txt; keep existing openpyxl.
- Rewrite src/backend/tasks/exports.py so:
    - CSV writes real .csv.
    - PDF writes real .pdf using ReportLab tables/paragraphs.
    - Excel writes real .xlsx using openpyxl.Workbook.
    - All export tasks validate requested columns through the existing allowlist plus
    new geography fields.
    - All export tasks insert an analytics_export_log row with requester, format,
    filters, columns, task/file metadata, row count, and timestamp.
- Add GET /api/analytics/export/{task_id} in src/backend/api/routes/analytics.py.
    - Require get_analyst_or_admin.
    - Resolve Celery task result path.
    - Return FileResponse with correct content type and filename.
    - Return 404/409 when the task is missing, pending, failed, or path is unavailable.
- Add frontend API helpers for queueing exports and downloading completed exports.
- Replace alert-only export UX with an export preview container showing active filters,
estimated included columns, and incident count preview before queueing.

### 2. Analytics Geography Migration

- Add next ordered SQL migration under src/postgres-init/, e.g.
28_analytics_geography_denorm.sql.
- Add municipality_name TEXT and province_name TEXT to wims.analytics_incident_facts
with IF NOT EXISTS.
- Update analytics sync paths in src/backend/services/analytics_read_model.py:
    - sync_incident_to_analytics
    - sync_incidents_batch
    - backfill_analytics_facts
- Populate new fields from incident_nonsensitive_details.city_municipality and
province_district.
- Extend export allowed columns and top-N dimension support with municipality.

### 3. Filter Options And Global Filter Contract

- Add GET /api/analytics/filter-options.
    - Params: field=province|municipality.
    - Optional filters: region_id, province, start_date, end_date.
    - Return string[], sorted, non-null/non-empty.
    - Enforce analyst/admin access.
- Extend analytics query functions and routes so all dashboard charts honor the same
global filters:
    - date range
    - region
    - province
    - municipality
    - incident type
    - alarm level
    - casualty severity
    - damage min/max
- Update src/frontend/src/lib/api.ts types and helpers to carry the expanded filter
shape consistently.
- Implement cascading frontend behavior:
    - Region limits province options.
    - Province limits municipality options.
    - No reverse auto-selection.
    - Clearing region clears province and municipality; clearing province clears
    municipality.

### 4. Dashboard Layout And Charts

- Install recharts in src/frontend.
- Update /dashboard/analyst layout:
    - Prominent filter bar at the top with sync status visually secondary.
    - Portrait/tall heatmap in a side column on desktop.
    - Data-dense chart/list area beside or below the heatmap depending on viewport.
- Replace AQ-06/AQ-07/AQ-08 list rows with Recharts:
    - Type distribution: donut or pie chart.
    - Top barangays: horizontal bar chart.
    - Response time by region: bar chart with avg and min/max in tooltip or secondary
    labels.
- Add top municipalities view through the existing top-N pattern using the new
municipality dimension.
- Keep accessible empty/loading/error states and stable chart dimensions.
- Add explicit NATIONAL_ANALYST navigation in Sidebar.tsx pointing to /dashboard/analyst
and profile.

### 5. Incident List Container

- Add analyst incident list API, preferably GET /api/incidents/analyst-list.
    - Require NATIONAL_ANALYST or SYSTEM_ADMIN.
    - Always filter fire_incidents.verification_status = 'VERIFIED' and is_archived =
    FALSE.
    - Query params: global filters, page, page_size, sort_by, sort_dir.
    - Allow sort only on listed columns: notification_dt, region, municipality_name,
    barangay_name, general_category, sub_category, alarm_level, estimated_damage_php,
    total_response_time_minutes.
    - Return { incidents, total, page, page_size }.
- Table columns:
    - notification date/time
    - region short name
    - municipality
    - barangay
    - general category
    - sub category
    - alarm level
    - estimated damage
    - response time
- Frontend behavior:
    - Place below charts under “Incident List”.
    - 25 rows/page.
    - Default sort notification_dt DESC.
    - Clickable sortable headers.
    - Row click opens a wide drawer, about 640px on desktop and full-screen on mobile.
    - Drawer shows key summary fields and an “Open Full Page” action to /dashboard/
    analyst/incidents/[id].

### 6. Analyst Detail Pages

- Add src/frontend/src/app/dashboard/analyst/incidents/[id]/page.tsx.
    - Read-only only.
    - No edit mode.
    - No validator actions.
    - Render common AFOR sections A-L using shared display helpers from the regional
    detail page where practical.
    - Include provenance: data_hash, created_at, encoder_id, reference number,
    verification status, and analytics sync fields when available.
    - Include Export PDF and Export CSV buttons for full AFOR output.
- Add backend analyst detail endpoint, preferably GET /api/incidents/analyst/
{incident_id}.
    - Require analyst/admin.
    - Return only verified, non-archived incidents.
    - Include common detail payload, provenance, attachments/sketch metadata, and
    whether wildland details exist.
- Add separate wildland analyst route/layout:
    - Route: /dashboard/analyst/incidents/[id]/wildland.
    - API can reuse the analyst detail endpoint if it includes wildland_afor, or expose
    GET /api/incidents/analyst/{incident_id}/wildland.
    - Show wildland-specific fields from incident_wildland_afor and related wildland
    tables.
    - Link to this route from the common detail page only when wildland data exists.

### 7. Wiki Updates

- Update synthesis pages, not system-wiki/raw/.
- Update:
    - system-wiki/backend/api-route-map.md
    - system-wiki/frontend/route-map.md
    - system-wiki/database/schema-overview.md
    - system-wiki/ui-ux/evaluation-national-analyst.md
    - system-wiki/gaps/ui-ux-gap-register.md
    - system-wiki/gaps/frs-codebase-gap-register.md
    - system-wiki/log.md
- Mark resolved items for export infrastructure, filter coverage, incident list, side
drawer/detail navigation, Recharts charts, top municipalities, response-time view, and
analyst sidebar.
- Keep scheduled reports as deferred unless separately requested.
- Add the thesis-wiki recommendation only as documentation: DB CHECK constraints for
general_category and sub_category as defense-in-depth, not implemented in this sprint.

## Public Interfaces

- GET /api/analytics/filter-options?field=province|
municipality&region_id=&province=&start_date=&end_date=
- GET /api/analytics/export/{task_id}
- GET /api/incidents/analyst-list
- GET /api/incidents/analyst/{incident_id}
- Optional if not folded into analyst detail payload: GET /api/incidents/analyst/
{incident_id}/wildland
- Frontend routes:
    - /dashboard/analyst
    - /dashboard/analyst/incidents/[id]
    - /dashboard/analyst/incidents/[id]/wildland

## Test Plan

- Backend pytest:
    - Export tasks create real CSV/PDF/XLSX files and write analytics_export_log.
    - Download endpoint enforces RBAC and returns correct content type.
    - Geography migration columns exist and sync/backfill populate municipality/
    province.
    - Filter-options endpoint returns scoped, sorted values and rejects invalid fields.
    - All analytics endpoints apply province/municipality/casualty/damage filters
    consistently.
    - Analyst incident list enforces VERIFIED-only, pagination, allowlisted sorting, and
    RBAC.
    - Analyst detail endpoints enforce RBAC and hide unverified/archived incidents.
    - Wildland detail returns wildland data only for matching incidents.
- Frontend Vitest/RTL:
    - Filter bar cascades region → province → municipality and clears dependent
    selections.
    - Recharts components replace fake list chart containers.
    - Incident list paginates, sorts, opens drawer, and navigates to full page.
    - Export preview passes active filters and download flow handles queued/completed
    states.
    - Analyst detail page renders read-only AFOR sections and no edit/validator
    controls.
    - Wildland link appears only when wildland data exists.
    - Sidebar includes a National Analyst section.
- Manual checks:
    - cd src/backend && pytest -v
    - cd src/frontend && npm run lint
    - cd src/frontend && npx vitest run
    - cd src/frontend && npm run build
    - Browser check for /dashboard/analyst desktop and mobile layouts.