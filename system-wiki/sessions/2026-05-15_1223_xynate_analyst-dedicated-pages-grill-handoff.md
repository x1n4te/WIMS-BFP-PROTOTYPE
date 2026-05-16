---
title: Analyst Dedicated Pages Grill Handoff
created: 2026-05-15
type: handoff
tags: [wims-bfp, handoff, national-analyst, analytics, ui-ux, grill-with-docs]
sources:
  - system-wiki/sessions/2026-05-15_1148_xynate_national-analyst-validation-keycloak-handoff.md
  - system-wiki/ui-ux/evaluation-national-analyst.md
  - system-wiki/gaps/ui-ux-gap-register.md
  - system-wiki/gaps/frs-codebase-gap-register.md
  - system-wiki/frontend/route-map.md
  - system-wiki/log.md
status: current
---

# Analyst Dedicated Pages Grill Handoff

## What Happened
- Read the prior handoff at `system-wiki/sessions/2026-05-15_1148_xynate_national-analyst-validation-keycloak-handoff.md`.
- Used `grill-with-docs` to clarify expected behavior for dedicated National Analyst workflow pages.
- Initial code was started before the user redirected back to grilling:
  - Added `src/frontend/src/app/dashboard/analyst/[workflow]/page.tsx`.
  - Added workflow launch cards to `src/frontend/src/app/dashboard/analyst/page.tsx`.
  - Added National Analyst workflow links to `src/frontend/src/components/Sidebar.tsx`.
  - Updated wiki route/gap/evaluation/log pages.
- Validation before the redirect:
  - `cd src/frontend && npm run lint` passed with pre-existing warnings outside the analyst slice.
  - `cd src/frontend && npx vitest run src/app/dashboard/analyst/page.test.tsx src/app/dashboard/analyst/queue-baseline.test.tsx` passed: `33 passed`.
  - `cd src/frontend && npm run build` passed only after network escalation for Google Fonts.
  - `cd src/frontend && npx tsc --noEmit` failed on pre-existing unrelated errors in admin/login/sync files, not the new analyst workflow route.
- The dev server was not left running. Attempts to start it hit sandbox bind/lock/port issues, then the user asked to stop.

## Decisions Captured
All decisions below were appended to `system-wiki/ui-ux/evaluation-national-analyst.md` and `system-wiki/log.md`.

1. Dedicated workflow pages should initialize their local filters from the active `/dashboard/analyst` global filters when opened from the overview dashboard.
2. Each dedicated workflow page needs a local reset/clear action that resets only that workflow page's filters and does not mutate overview dashboard filters.
3. Comparative analysis uses the same non-date global/local filters for both periods; only `Range A` and `Range B` date windows differ.
4. The dashboard incident list must become more prominent and support selecting incidents for analysis/export.
5. Dashboard selections persist across pagination while filters remain unchanged.
6. The dedicated incident-explorer page should show 100 rows per page for dense review.
7. Normal workflow-card navigation transfers filters only.
8. Explicit "Analyze selected" transfers filters plus selected incident IDs into a workflow page.
9. Workflow pages with selected IDs need a selected-set banner; local reset clears selected IDs.
10. Selected-record CSV/PDF export uses a dedicated column-selection modal.
11. Full AFOR export means all AFOR fields/columns, not just visible list columns.
12. Multi-incident full AFOR PDF export should be one combined PDF with each incident starting on a new page or clearly separated section.
13. Full AFOR CSV should be one row per incident with all AFOR fields flattened into stable columns.
14. Repeating/nested AFOR sections should serialize into readable semicolon-separated cell values.
15. Heatmap/geospatial workflow should follow map/global filters and selected map area.
16. The heatmap workflow's incident table should follow both active map filters and selected map area.
17. Recommended heatmap local controls: map metric, aggregation level, intensity mode, incident pin toggle, administrative-boundary toggle, and map snapshot export.

## Important Implementation Caveat
Selected incident IDs should not be shown as affecting aggregate charts until backend analytics endpoints support explicit incident ID sets. Until then, selected IDs can safely drive tables and exports, while aggregate charts must be labeled as filtered-population calculations.

## Current Dirty Files
At handoff time, the worktree had these relevant changes:
- `src/frontend/src/app/dashboard/analyst/[workflow]/page.tsx` (new)
- `src/frontend/src/app/dashboard/analyst/page.tsx`
- `src/frontend/src/components/Sidebar.tsx`
- `system-wiki/frontend/route-map.md`
- `system-wiki/gaps/frs-codebase-gap-register.md`
- `system-wiki/gaps/ui-ux-gap-register.md`
- `system-wiki/index.md`
- `system-wiki/log.md`
- `system-wiki/ui-ux/evaluation-national-analyst.md`
- this handoff file

## Suggested Next Session
Use `grill-with-docs` first if continuing product decisions. The next unresolved decisions should cover:
- Exact controls and outputs for Trends, Response Time, Top-N, and Incident Explorer dedicated pages.
- Whether selected incident IDs should be encoded in query params, session storage, or a frontend state store when transferring to workflow pages.
- Backend API shape for selected-record export and full AFOR export.
- Backend API shape for ID-scoped analytics if aggregate charts must honor selected incident sets.

Use `karpathy-guidelines` before implementation. Keep changes surgical and avoid broad frontend refactors.

## Suggested Implementation Direction
- Make selected incident sets explicit in the `AnalystIncidentList` component API.
- Add a selected-count action bar with `Analyze selected`, `Export selected columns`, `Export full AFOR`, and `Clear selection`.
- Add a configurable page size prop so dashboard can remain 25 rows/page and incident explorer can use 100 rows/page.
- Use URL query params for small filter handoff; avoid putting large selected ID sets directly in the URL unless capped. For larger selections, prefer session storage keyed by a short transfer ID.
- Add backend/export tests before wiring UI export buttons, especially for selected IDs and full AFOR flattening.

## Do Not Forget
- Do not edit `system-wiki/raw/`.
- Update synthesis pages plus `system-wiki/log.md` when decisions or implementation facts change.
- The local runtime previously had `0` incidents/facts, so empty analyst lists are expected unless data is seeded/imported/verified.
