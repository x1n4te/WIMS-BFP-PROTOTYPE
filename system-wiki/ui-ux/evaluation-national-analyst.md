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
**Status:** Resolved in code: `/dashboard/analyst` now renders an Incident List section backed by `GET /api/incidents/analyst-list`, with pagination, sort headers, and global filters.
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
**Status:** Fixed in code: `/dashboard/analyst` renders `ResponseTimeChart` backed by `GET /api/analytics/response-time-by-region`.
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

**Execution order (per #89):** Phase 0 → Phase 1 → Phase 2/3 (parallel) → Phase 5 → Phase 4

## Related
- [[ui-ux/evaluation-loginpage-keycloaksso]]
- [[ui-ux/evaluation-system-admin-hub]]
- [[gaps/ui-ux-gap-register]]
- [[gaps/functional-bug-register]]
- [[concepts/frs-module-map]] — M5 (Analytics) and M12 (User Management) routing
- [[backend/api-route-map]] — analytics routes
- [[frontend/route-map]] — `/dashboard/analyst` page
