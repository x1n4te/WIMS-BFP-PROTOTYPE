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
- National Analyst dashboard implementation: Phase 0-6 code paths are implemented for analytics sync, export infrastructure, geography filters, Recharts charts, incident list/drawer, read-only incident detail, wildland detail, dashboard export preview, side-column heatmap layout, and prominent filter labels.
- Export audit/download pipeline: CSV/PDF/XLSX task writers, dashboard preview/download UX, and `GET /api/analytics/export/{task_id}` are implemented; verify Celery result backend retention and export-file cleanup policy before production use.
- Analyst incident drill-down: `GET /api/incidents/analyst-list`, `GET /api/incidents/analyst/{incident_id}`, and `GET /api/incidents/analyst/{incident_id}/wildland` are implemented for verified, non-archived incidents behind analyst/admin RBAC and RLS. Verify seeded data covers wildland examples and full browser flows before production use.
- RLS enforcement: verify role-region scoping through helpers and policies.
- Public DMZ abuse controls: verify unauthenticated route has rate limiting/input validation and cannot bypass triage.
- Notifications: verify SSE/Redis/email behavior against Module 13.
- Offline-first: verify IndexedDB encryption/sync semantics against Module 2.
- M9 System Monitoring: verify psutil/Docker API metrics collection, 60s refresh, and full-text log search (NOT yet implemented).

## Related
- [[concepts/frs-module-map]]
- [[security/security-baseline]]
- [[gaps/ui-ux-gap-register]]
- [[gaps/functional-bug-register]]
