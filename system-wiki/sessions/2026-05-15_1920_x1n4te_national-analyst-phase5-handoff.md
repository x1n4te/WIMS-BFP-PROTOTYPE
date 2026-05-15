---
title: National Analyst Phase 5 Handoff
created: 2026-05-15
updated: 2026-05-15
type: session
tags: [wims-bfp, handoff, national-analyst, phase-5, incidents, detail]
sources:
  - system-wiki/plan/National-Analyst-Plan.md
  - system-wiki/log.md
  - system-wiki/backend/api-route-map.md
  - system-wiki/frontend/route-map.md
status: in-progress
---

# National Analyst Phase 5 Handoff

## Session context

This session continued from the Phase 4 handoff (`system-wiki/sessions/2026-05-15_0215_x1n4te_national-analyst-frontend-phase4-handoff.md`). It completed p4-8 (TrendCharts Recharts LineChart) and p4-9 (test updates), committed them, then started Phase 5 implementation.

## What changed

### Phase 4 completion

- **p4-8**: Replaced `TrendCharts.tsx` custom SVG bar rendering with `LineChart` from recharts — monotone stroke, BFP-red `#991b1b`, CartesianGrid, proper XAxis/YAxis with interval preservation, Tooltip with count label.
- **p4-9**: Updated `page.test.tsx` to mock `fetchAnalyticsFilterOptions` (was missing — caused cascade effect errors in vitest). Updated `TrendCharts.test.tsx` to check for `.recharts-responsive-container` instead of text nodes (Recharts doesn't render count labels as text nodes).
- Committed: `08185c1 feat(analyst): p4-8 replace TrendCharts SVG with Recharts LineChart` and pushed to `feature/national-analyst-dashboard`.

### Phase 5 backend (p5a + p5e)

Implemented in `src/backend/api/routes/incidents.py`:

**`GET /api/incidents/analyst-list`** (p5a):
- Requires `NATIONAL_ANALYST` or `SYSTEM_ADMIN` (via `get_analyst_or_admin`).
- Always filters `verification_status = 'VERIFIED'` and `is_archived = FALSE`.
- Accepts global filter params: `start_date`, `end_date`, `region_id`, `province`, `municipality`, `incident_type`, `alarm_level`, `casualty_severity`, `damage_min`, `damage_max`.
- Pagination: `page` (default 1), `page_size` (default 25, max 100).
- Sortable columns (allowlisted): `notification_dt`, `region`, `municipality_name`, `barangay_name`, `general_category`, `sub_category`, `alarm_level`, `estimated_damage_php`, `total_response_time_minutes`. Default: `notification_dt DESC`.
- Returns `{ incidents, total, page, page_size }`.
- Uses denormalized `municipality_name` from `analytics_incident_facts` (Geography Denorm migration `28_analytics_geography_denorm.sql`).

**`GET /api/incidents/analyst/{incident_id}`** (p5e):
- Requires `NATIONAL_ANALYST` or `SYSTEM_ADMIN`.
- Returns 404 if incident is not `VERIFIED` or is `archived`.
- Includes key fields: incident_id, notification_dt, region, municipality_name, barangay_name, general_category, sub_category, alarm_level, estimated_damage_php, total_response_time_minutes, verification_status, created_at.
- Includes provenance: `data_hash`, `encoder_id`, reference number, analytics sync fields.
- Includes `has_wildland_afor` boolean (checks `incident_wildland_afor` table existence).

## Current branch state

```
feature/national-analyst-dashboard
├── 08185c1 feat(analyst): p4-8 replace TrendCharts SVG with Recharts LineChart  (committed + pushed)
├── ... (in-progress Phase 5 work — not yet committed)
```

## Files changed this session

- `src/backend/api/routes/incidents.py` — added `GET /api/incidents/analyst-list` and `GET /api/incidents/analyst/{incident_id}`
- `src/frontend/src/components/analytics/TrendCharts.tsx` — Recharts LineChart replacement
- `src/frontend/src/components/analytics/TrendCharts.test.tsx` — updated for Recharts container check
- `src/frontend/src/app/dashboard/analyst/page.test.tsx` — added `fetchAnalyticsFilterOptions` mock

## Remaining Phase 5 work

### Still pending

1. **p5b — Frontend incident list table on `/dashboard/analyst`**
   - Add `IncidentList` section below charts on `src/frontend/src/app/dashboard/analyst/page.tsx`.
   - 25 rows/page, default sort `notification_dt DESC`.
   - Sortable column headers.
   - Row click → wide drawer (~640px desktop, full-screen mobile).
   - Drawer: key summary fields + "Open Full Page" link to `/dashboard/analyst/incidents/[id]`.
   - Wire to `GET /api/incidents/analyst-list`.

2. **p5c — `/dashboard/analyst/incidents/[id]` detail page**
   - New route: `src/frontend/src/app/dashboard/analyst/incidents/[id]/page.tsx`.
   - Read-only, no edit/validator controls.
   - Render key AFOR summary fields from the incident detail API.
   - Include provenance: data_hash, created_at, encoder_id, reference number, verification status.
   - Include Export PDF and Export CSV buttons (wire to existing export endpoints).

3. **p5d — `/dashboard/analyst/incidents/[id]/wildland` route**
   - New route: `src/frontend/src/app/dashboard/analyst/incidents/[id]/wildland/page.tsx`.
   - Shows wildland-specific fields from `incident_wildland_afor` and related tables.
   - Link to this route from the common detail page only when `has_wildland_afor = true`.
   - Backend may need `GET /api/incidents/analyst/{incident_id}/wildland` or can fold wildland data into the analyst detail endpoint.

4. **Frontend API helpers**
   - Add `fetchAnalystIncidentList(filters, page, page_size, sort_by, sort_dir)` to `src/frontend/src/lib/api.ts`.
   - Add `fetchAnalystIncidentDetail(incidentId)` to `src/frontend/src/lib/api.ts`.

5. **Wiki updates**
   - Update `system-wiki/backend/api-route-map.md` with new endpoints.
   - Update `system-wiki/frontend/route-map.md` with new routes.
   - Update `system-wiki/ui-ux/evaluation-national-analyst.md` to mark items resolved.
   - Update `system-wiki/gaps/ui-ux-gap-register.md` and `system-wiki/gaps/frs-codebase-gap-register.md`.
   - Log in `system-wiki/log.md`.

## Watch points

- `analytics_incident_facts.municipality_name` / `province_name` must be populated by the migration `28_analytics_geography_denorm.sql` before the analyst-list query uses them — they come from `incident_nonsensitive_details.city_municipality` and `province_district`.
- `get_db_with_rls` must be used (not plain `get_db`) so RLS policies apply to analyst endpoints.
- `get_analyst_or_admin` enforces `NATIONAL_ANALYST` or `SYSTEM_ADMIN` on both new endpoints.
- The sort allowlist in analyst-list is strict — only the 9 columns listed in the plan are allowed.

## Skills to use next session

- `karpathy-guidelines`: apply before writing new frontend components to keep changes surgical.
- `wims-bfp-project-context`: ensure clean context isolation for the National Analyst work.
- `github:yeet`: when the branch is ready to commit, push, and open a draft PR.
- Do NOT use image generation skills — not needed for this work.

## Execution order

Phase 5 remaining in order: p5b (incident list table + drawer) → p5c (detail page) → p5d (wildland) → wiki updates. Each phase depends on the previous API contract being stable.