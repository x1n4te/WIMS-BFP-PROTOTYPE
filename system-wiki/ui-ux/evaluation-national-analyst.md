---
title: "National Analyst Dashboard — UX Evaluation"
created: 2026-05-14
updated: 2026-05-15
type: evaluation
tags: [wims-bfp, ui-ux, national-analyst, dashboard, m5]
sources: [raw/ui-ux/evaluation-national-analyst.md]
status: open
---

# National Analyst Dashboard — UX Evaluation

Source: User desk-check notes (`raw/ui-ux/evaluation-national-analyst.md`).

---

## Layout Issues

### L-01 — Heatmap aspect ratio is wrong; wastes horizontal space
**Current:** Wide, full-width heatmap spanning the top of the dashboard.
**Expected:** Tall (portrait) heatmap positioned on the side (left or right column), not spanning the full width. This allows the layout to use vertical space more efficiently for a data-dense analyst view.
**Status:** Fixed in code: `/dashboard/analyst` now uses a desktop two-column grid with the heatmap in a 360px side column and the chart/list/export workflow in the main column. Browser layout verification remains recommended.
**Priority:** HIGH — layout restructure needed.

### L-02 — Filter bar sizing and alignment
**Current:** Filters are inline with "All Synced" status indicator but are the same size.
**Expected:** Filters should be larger and more prominent than the "All Synced" badge. The filter bar should sit at the top of the content area, inline with the sync status, but visually dominant.
**Status:** Fixed in code: analyst filter labels were raised from tiny uppercase labels to `text-sm font-semibold`; the sync badge is no longer the visual peer of the filter controls.
**Priority:** MEDIUM.

### L-03 — No individual incident container
**Current:** No container or list view for individual incidents.
**Expected:** A dedicated incident list panel must exist on the dashboard — distinct from the heatmap and trend charts. This panel must be filterable.
**Status:** Resolved in code: `/dashboard/analyst` now renders an Incident List section backed by `GET /api/incidents/analyst-list`, with pagination, sort headers, and global filters. The dedicated `/dashboard/analyst/incident-explorer` workflow also uses this verified incident table as the primary page surface.
**Priority:** HIGH.

### L-04 — Side panel for incidents is non-functional
**Current:** Any side panel or drawer for viewing incident details redirects back to the dashboard.
**Expected:** Clicking an incident in the list should open a functional detail panel (slide-over or dedicated route) showing full incident data.
**Status:** Resolved in code: incident rows open a wide drawer with key summary fields and an "Open Full Page" link to `/dashboard/analyst/incidents/[id]`; wildland AFOR records link to `/dashboard/analyst/incidents/[id]/wildland`.
**Priority:** HIGH.

---

## Filter Issues

### F-01 — Filter does not cover all incident schema columns
**Current:** Filters cover only incident type, alarm level, and interval.
**Required (per FRS M5.a.ii):**
- Date range (from–to)
- Incident type
- Location (municipality, province, region)
- Casualty severity
- Property damage range
**Additional (per FRS M5 for wildfires — planning needed):**
- Fire cause/origin
- Weather conditions at time of incident
- Suppression resources deployed
**Status:** Core M5 filter contract fixed in code for analytics dashboard endpoints: date range, region, province, municipality, incident type, alarm level, casualty severity, and property damage range are wired through the dashboard, API helpers, and analytics read model. Wildfire-specific filter expansion remains future scope.
**Priority:** HIGH — FRS compliance gap. Filter must be expanded to match the full `fire_incidents` schema and planned `wildfire_incidents` schema.

### F-02 — No export preview container
**Current:** Export PDF and Export Excel buttons export immediately without showing what will be included.
**Expected:** A dedicated container/section above the export buttons should show a quick overview of what data will be included — query parameters applied, date range, incident count preview — before triggering the export. This container should also expose filters specific to the export (e.g., date range, incident type, region).
**Status:** Fixed in code: dashboard export buttons now open `ExportPreviewModal` for CSV/PDF/Excel, showing active filters, selectable backend-allowed columns, queue/poll/download state, and using `POST /api/analytics/export/{format}` plus `GET /api/analytics/export/{task_id}`.
**Priority:** HIGH.

---

## Gaps Not Explicitly Raised by User (from FRS + GitHub Issue #89)

These are confirmed missing by cross-referencing FRS M5 and GitHub Issue #89. User did not explicitly list these in their desk check notes but they are part of the analyst dashboard scope.

### G-01 — Top municipalities view missing
**FRS M5.a.iii:** "Top 10 municipalities with highest incident count" is a required analytics view. Not present in current `analyst/page.tsx`.
**Status:** Fixed in code: Top-N analysis supports `dimension=municipality` via `analytics_incident_facts.municipality_name`.
**Priority:** HIGH.

### G-02 — Average response time by region view missing
**FRS M5.a.iii:** "Average response time by region" is a required analytics view. Not present in current `analyst/page.tsx` (response time is listed in imports but not rendered).
**Status:** Fixed in code: `/dashboard/analyst` renders `ResponseTimeChart` backed by `GET /api/analytics/response-time-by-region`; `/dashboard/analyst/response-time` provides a dedicated response-time workflow with min/max/average summary, export actions, and matching incident table.
**Priority:** HIGH.

### G-03 — Phase 0: verify_incident() missing analytics sync (P0 CRITICAL)
**Issue #84:** When a National Validator accepts an incident (PENDING → VERIFIED), `sync_incident_to_analytics()` is NOT called. The incident never appears in the analyst dashboard. This blocks all analyst features.
**Status:** Fixed in live code before this pass; `regional.py` calls `sync_incident_to_analytics()` after VERIFIED transitions and replacement archival paths. Keep regression coverage.
**Priority:** P0 CRITICAL — monitor as a regression target.

### G-04 — Export infrastructure incomplete (Phase 1)
**Issue #85:** PDF export writes HTML to `.html` file (not a real PDF). Excel export writes CSV with wrong extension. No HTTP download endpoint. Export audit trail not wired.
**Status:** Backend infrastructure implemented in this pass: real CSV/PDF/XLSX writers, `GET /api/analytics/export/{task_id}`, export metadata/audit insert path, and export-log schema expansion. Frontend preview/download UX remains pending.
**Priority:** P1 HIGH.

### G-05 — Charts not upgraded to Recharts (Phase 3)
**Issue #87:** Type distribution (AQ-06), top barangays (AQ-07), and response time (AQ-08) still render as HTML table rows instead of Recharts visualizations.
**Status:** Fixed in code: `TypeDistributionChart`, `TopBarangaysChart`, `ResponseTimeChart`, and `TrendCharts` now use Recharts.
**Priority:** P2 MEDIUM.

### G-06 — Scheduled reports not implemented (Phase 4)
**Issue #88:** `scheduled_reports` table exists but no Celery task, no admin CRUD API, no email delivery, no admin UI.
**Priority:** P3 MEDIUM.

### G-07 — Sidebar lacks NATIONAL_ANALYST section
**Issue #86:** `Sidebar.tsx` `getNavSections()` has no explicit `NATIONAL_ANALYST` case — falls through to default generic links.
**Status:** Fixed in `src/frontend/src/components/Sidebar.tsx`; explicit National Analyst navigation now points to `/dashboard/analyst` and `/profile`.
**Priority:** P2 MEDIUM.

### G-08 — No integration testing (Phase 5)
**Issue #89 Phase 5:** Smoke test and integration testing after phases 0–3 complete. Not yet planned.
**Priority:** P1 HIGH (gated on phases 0–3).

---

## Summary

| ID | Issue | Type | Priority | FRS Ref |
|---|---|---|---|---|
| L-01 | Heatmap aspect ratio — portrait, side-positioned | Layout | HIGH | M5 |
| L-02 | Filter bar sizing — larger than sync badge | Layout | MEDIUM | M5 |
| L-03 | No incident container/list | Layout | HIGH | M5 |
| L-04 | Side panel non-functional (redirects) | Functional | HIGH | M5 |
| F-01 | Filter missing columns (date range, casualty, damage, location) | Filter gap | HIGH | M5.a.ii |
| F-02 | Export has no preview container | UX | HIGH | M5.c |
| G-01 | Top municipalities view missing | Missing view | HIGH | M5.a.iii |
| G-02 | Average response time by region missing | Missing view | HIGH | M5.a.iii |
| G-03 | verify_incident() no analytics sync | Data pipeline | P0 CRITICAL | M5 / #84 |
| G-04 | Export infrastructure incomplete | Backend | P1 HIGH | M5.c / #85 |
| G-05 | Charts not upgraded to Recharts | Frontend | P2 MEDIUM | M5.a.iii / #87 |
| G-06 | Scheduled reports not implemented | Backend | P3 MEDIUM | M5 / #88 |
| G-07 | Sidebar missing NATIONAL_ANALYST section | Frontend | P2 MEDIUM | M12 / #86 |
| G-08 | No integration testing | Testing | P1 HIGH | #89 Phase 5 |

Phase 5 implementation note (2026-05-14): analyst incident list, sortable drawer, read-only incident detail page, and read-only wildland detail route are implemented.

Phase 7 validation note (2026-05-14): Phases 0-6 are implemented in code, including dashboard export preview/download, CSV/PDF/Excel entry points, side-column heatmap, prominent filter labels, Recharts charts, top municipalities, response-time view, incident list/drawer/detail/wildland routes, and analyst sidebar. Remaining verification: full browser UI pass and full backend integration test pass in a non-hanging environment.

Manual validation follow-up (2026-05-15): User reported `/dashboard/analyst` showing "All synced" while the Incident List returned `Request failed: 500`. Root cause was a backend analyst incident SQL/schema mismatch in `src/backend/api/routes/incidents.py`: the list/detail queries referenced `nd.barangay`, `r.short_name`, and analytics columns not present in `wims.analytics_incident_facts`. Code now uses `ref_barangays` / `aif.barangay_name`, `ref_regions.region_code` / `region_name`, derives casualty severity from casualty count columns, reads `data_hash` from `fire_incidents`, and exposes a derived analytics sync status. Focused regression coverage added in `src/backend/tests/test_analyst_incidents_sql_contract.py`.

Runtime data note (2026-05-15): After container rebuild/restart, local Postgres showed `0` rows in `wims.fire_incidents` and `0` rows in `wims.analytics_incident_facts`; the dashboard therefore correctly has no visible incidents until incidents are created, submitted, verified, and synced/backfilled.

UI/UX overhaul note (2026-05-15): `/dashboard/analyst` was reorganized for HCI-friendly scanning: top summary tiles, grouped filters, clearer apply/reset controls, export preview actions, icon-led panel headers, sticky portrait heatmap, and a friendlier incident-list error state. Frontend analyst Vitest suites pass; browser verification remains recommended.

Dedicated workflow note (2026-05-15): `/dashboard/analyst/[workflow]` now provides focused analyst pages for `comparative`, `heatmap`, `trends`, `response-time`, `top-n`, and `incident-explorer`. Each workflow keeps analyst/admin RBAC, shared global filters, CSV/PDF/Excel export preview actions, calculation/detail context where applicable, and the verified incident table so deeper analysis no longer has to live only on the overview dashboard.

Dedicated workflow filter decision (2026-05-15): when a National Analyst opens a dedicated workflow page from `/dashboard/analyst`, the active overview/global filters should transfer into that workflow page's local filter inputs. Each workflow page must also provide a local reset/clear action so the analyst can clear the workflow-local filters without changing the overview dashboard's current filter state.

Comparative workflow decision (2026-05-15): comparative analysis uses one shared population filter contract for both periods. `Range A` and `Range B` differ only by their date windows; all other local/global filters apply equally to both periods so the variance is defensible.

Incident-list analysis decision (2026-05-15): the analyst dashboard needs a more prominent incident list surface that can produce a selected incident set for analysis and export. Analysts should be able to select incidents from the list and export only those selected records to CSV and PDF, separate from exporting the full filtered analytics result.

Incident-list pagination decision (2026-05-15): selected incidents on the dashboard list must persist across dashboard pagination while the current filters remain unchanged. The dedicated incident-explorer workflow page should use a denser review table with 100 rows per page visible, instead of the dashboard's 25-row page size.

Selected-set workflow transfer decision (2026-05-15): normal workflow-card navigation transfers only the active global filters. An explicit "Analyze selected" action from the dashboard incident list should transfer both active filters and selected incident IDs into a dedicated workflow page. The workflow page must show that it is analyzing a selected set, local reset must clear those selected IDs, and CSV/PDF exports should default to the selected IDs while they are present. Charts/calculations may honor selected IDs only after backend analytics endpoints support ID-scoped queries; until then the UI must clearly distinguish filtered-population calculations from selected-record exports/tables.

Selected export decision (2026-05-15): selected-record CSV/PDF export should open a dedicated column-selection modal so analysts choose which list/table columns appear in the file. Full AFOR export means all AFOR fields/columns are included for the selected incidents, not only the visible list columns. Multi-incident full AFOR PDF export should generate one combined PDF, with each incident starting on a new page or clearly separated section.

Full AFOR CSV decision (2026-05-15): full AFOR CSV export should produce one row per incident with all AFOR fields flattened into stable columns. Repeating or nested AFOR sections such as responding units, involved parties, operational challenges, attachments, and wildland assistance rows should serialize into readable semicolon-separated cell values rather than creating multiple incident rows.

Heatmap/geospatial workflow decision (2026-05-15): the dedicated heatmap workflow should follow the shared map/global filters and support selecting a map area so the incident table below follows both the map filters and selected map area. Recommended local heatmap controls are map metric, aggregation level, intensity mode, incident pin toggle, administrative-boundary toggle, and map snapshot export.

Selected-set transfer mechanism decision (2026-05-16): selected incident handoff from the overview dashboard to a dedicated workflow should use `sessionStorage` plus a short transfer ID in the URL. The dashboard writes active filters and selected incident IDs under a key such as `analyst-workflow-transfer:{uuid}`, navigates to `/dashboard/analyst/{workflow}?transfer={uuid}`, and the workflow page initializes local filters and selected IDs from that browser-local transfer payload.

Trends workflow decision (2026-05-16): the dedicated Trends page should support interval granularity of daily, weekly, monthly, quarterly, and yearly. It should also provide manual date-range inputs, expressed as Range A to Range B, so analysts can define the exact trend window independently of the inherited overview dates. Recommended local controls include measure (incident count, estimated damage, casualties, average response time), optional compare-by split (none, incident type, alarm level, region, province, municipality), and rolling average (off, 7-day, 30-day). Outputs should include the trend chart, summary tiles for total/peak/lowest/change, and the matching incident evidence table.

Response-time workflow decision (2026-05-16): the dedicated Response Time page should use `total_response_time_minutes` as the primary metric and break response timing down further only when component timestamps exist. Recommended local controls are group-by dimension (region, province, municipality, fire station, incident type), statistic (average, median, min/max, 90th percentile), target-threshold minutes input, exclude-incomplete-timestamps toggle defaulting on, and an editable local date range inherited from global filters. Outputs should include grouped response-time charting, tiles for average/median/fastest/slowest/percent-within-threshold, an outlier table for slowest incidents, and the main incident evidence table.

Top-N workflow decision (2026-05-16): the dedicated Top-N / Hotspot page should default to Top 10 municipalities by incident count. Local controls should include dimension (municipality, barangay, province, region, fire station, incident type, alarm level, fire cause when available), metric (incident count, estimated damage, casualties, average response time), N (5, 10, 20, 50, custom), and sort direction. Do not include a minimum incident count threshold; the page should show the truthful ranking even when sample sizes are small. Outputs should include ranked horizontal bar chart, ranked table with rank/name/metric/incident-count/share-of-total, click-to-filter incident table behavior, and ranking plus evidence export.

Incident Explorer workflow decision (2026-05-16): the dedicated Incident Explorer should be the selected-set control center, not only a table. It should inherit shared local filters, show 100 rows per page, support column visibility, sortable columns, row selection across pagination, quick search when backend support exists, wide drawer/detail navigation, selected-count action bar, Analyze Selected, selected-column CSV/PDF export, full AFOR export, and Clear Selection.

Selected export architecture decision (2026-05-16): selected incident/AFOR exports should use a parallel modular export system instead of extending the existing analytics aggregate export endpoint. Rationale: selected-record and full-AFOR exports have different payload shape, flattening rules, and failure modes; keeping them separate reduces the existing analytics export endpoint as a single point of failure.

Selected export API decision (2026-05-16): the MVP selected incident export module should live under the analyst incident route group. Proposed endpoints are `POST /api/incidents/analyst/export` to queue export generation and `GET /api/incidents/analyst/export/{task_id}` to download the generated file. Request body should include `incident_ids`, `export_mode` (`selected_columns` or `full_afor`), `format` (`csv` or `pdf`), and `columns` for selected-column export. Backend must enforce analyst/admin RBAC, re-check that selected incidents are verified and non-archived, allowlist selected columns, ignore columns for full AFOR export, and log requester/count/mode/format/columns/file metadata/timestamp. Explicit status endpoint `GET /api/incidents/analyst/export/{task_id}/status` is a future enhancement after the MVP dashboard.

Incident export scope decision (2026-05-16): the new incident export module should support both explicit selected IDs and the current filtered result. UI actions should be labeled separately as "Export selected" and "Export current result". Export current result must apply the local filters across all matching verified incidents, not only the current page, and should show an estimated-count confirmation before queueing.

Dedicated workflow export scope decision (2026-05-16): every dedicated analyst workflow page should be able to export its current filtered result, not only Incident Explorer. Export UI must clearly label scope and mode, including selected incidents, current filtered result, full AFOR for selected incidents, and full AFOR for current result. Large full-AFOR current-result exports should be queued asynchronously with stronger confirmation.

Selected-ID analytics MVP decision (2026-05-16): MVP aggregate charts/calculations should remain filter-scoped, not selected-ID-scoped. Selected incident IDs should drive table/export behavior only in MVP. UI copy must clearly state that charts use current filters while selected exports use selected incidents. Backend ID-scoped aggregate analytics is a post-MVP enhancement.

Dedicated workflow MVP phasing decision (2026-05-16): implement dedicated analyst workflow improvements in two phases. Phase 1 should cover workflow UI and selection: filter handoff via `sessionStorage` transfer ID, local reset, more prominent dashboard incident list, selection across pagination, Incident Explorer as a 100-row selected-set control center, dedicated workflow pages with filter-scoped charts/evidence tables, and clear labels that charts use filters while exports may use selected/current-result scopes. Phase 2 should cover the modular incident export backend: `POST /api/incidents/analyst/export`, `GET /api/incidents/analyst/export/{task_id}`, selected/current-result scopes, selected-column CSV/PDF modal, full AFOR CSV/PDF export, export audit logging, and backend/frontend tests for RBAC, verified/non-archived enforcement, flattening, and file generation.

Phase 1 implementation note (2026-05-16): workflow UI and selection are implemented in code. `/dashboard/analyst` now transfers current filter state into workflow cards via `sessionStorage` transfer IDs, the dashboard incident list is more prominent, row selection persists across pagination until filters change, "Analyze selected" transfers selected IDs to a workflow, and `/dashboard/analyst/incident-explorer` uses a 100-row evidence table. Dedicated workflow pages read transfer payloads, provide local reset, show selected-set labeling, keep charts filter-scoped, pass selected IDs into the evidence table when entered through "Analyze selected", and label Phase 2 export boundaries. `GET /api/incidents/analyst-list` now accepts comma-separated `incident_ids` for selected-set evidence tables. Trends now accepts daily/weekly/monthly/quarterly/yearly intervals.

**Execution order (per #89):** Phase 0 → Phase 1 → Phase 2/3 (parallel) → Phase 5 → Phase 4

## Related
- [[ui-ux/evaluation-loginpage-keycloaksso]]
- [[ui-ux/evaluation-system-admin-hub]]
- [[gaps/ui-ux-gap-register]]
- [[gaps/functional-bug-register]]
- [[concepts/frs-module-map]] — M5 (Analytics) and M12 (User Management) routing
- [[backend/api-route-map]] — analytics routes
- [[frontend/route-map]] — `/dashboard/analyst` page
