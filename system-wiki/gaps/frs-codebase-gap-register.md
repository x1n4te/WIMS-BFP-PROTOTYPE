---
title: FRS Codebase Gap Register
created: 2026-05-14
updated: 2026-05-14
type: gap
tags: [wims-bfp, gap, frs, needs-verification]
sources: [raw/frs, raw/codebase/codebase-snapshot-2026-05-14.md]
status: needs-review
---

# FRS Codebase Gap Register

This register prevents agents from hallucinating completion. A module is not complete just because a route or table exists.

## High-Risk Verification Targets
- Immutable record hashing: verify whether `data_hash` covers all required incident/provenance fields.
- Analytics sync on verification/correction: verify transaction boundaries and error handling.
- Analytics geography filters: `analytics_incident_facts` now has denormalized `municipality_name` and `province_name` via `28_analytics_geography_denorm.sql`; verify deployed databases are migrated and backfilled.
- National Analyst dashboard implementation: Phase 0-6 code paths are implemented for analytics sync, export infrastructure, geography filters, Recharts charts, incident list/drawer, read-only incident detail, wildland detail, dashboard export preview, side-column heatmap layout, prominent filter labels, and dedicated workflow pages for comparative analysis, heatmap/geospatial review, trends, response time, top-N hotspots, and incident explorer. Phase 1 workflow UI/selection is implemented; Phase 2 modular selected/full-AFOR export backend remains.
- Export audit/download pipeline: CSV/PDF/XLSX task writers, dashboard preview/download UX, and `GET /api/analytics/export/{task_id}` are implemented; verify Celery result backend retention and export-file cleanup policy before production use.
- Analyst incident drill-down: `GET /api/incidents/analyst-list`, `GET /api/incidents/analyst/{incident_id}`, and `GET /api/incidents/analyst/{incident_id}/wildland` are implemented for verified, non-archived incidents behind analyst/admin RBAC and RLS. Verify seeded data covers wildland examples and full browser flows before production use.
- Selected-set analytics: future selected-incident analysis requires backend analytics support for explicit incident ID sets. MVP keeps aggregate charts filter-scoped and uses selected IDs for evidence-table behavior, with UI labeling that selected IDs do not affect aggregate chart calculations. Selected-record/full-AFOR export remains a Phase 2 backend module.
- Selected incident export module: selected-record and full-AFOR exports should be implemented as a parallel modular export system, not by extending the existing aggregate analytics export endpoint.
- RLS enforcement: verify role-region scoping through helpers and policies.
- Public DMZ abuse controls: verify unauthenticated route has rate limiting/input validation and cannot bypass triage.
- Notifications: verify SSE/Redis/email behavior against Module 13.
- Offline-first: verify IndexedDB encryption/sync semantics against Module 2.
- M9 System Monitoring: verify psutil/Docker API metrics collection, 60s refresh, and full-text log search (NOT yet implemented).
- TOP-N barangay dimension: PARTIALLY RESOLVED / DEFERRED — `src/postgres-init/31_barangay_geometry.sql` adds `geometry GEOGRAPHY(POLYGON, 4326)` column + GiST index to `ref_barangays`, and `src/backend/api/routes/regional.py` contains `_reverse_geocode_barangay(db, incident_id, lon, lat)` hooks for AFOR/manual incident creation. This remains optional because no reliable local barangay polygon seed exists in the repo. A proposed `load-barangay-geometries` one-shot Docker/GitHub PSGC loader was rejected on 2026-05-16: it made stack startup network-dependent, removed/broke existing Docker services and environment values, and attempted invalid PSGC SQL (`NULL` `city_id` inserts into `ref_barangays`). Analyst Top-N UI should prefer `municipality`, `fire_station`, and `region`; barangay ranking should stay deferred until a vetted local polygon/reference-data import is designed.

## Related
- [[concepts/frs-module-map]]
- [[security/security-baseline]]
- [[gaps/ui-ux-gap-register]]
- [[gaps/functional-bug-register]]
