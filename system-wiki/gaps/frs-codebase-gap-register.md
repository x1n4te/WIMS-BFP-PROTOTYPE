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
- M9 System Monitoring: 🟡 PARTIAL — PR #103 adds Prometheus /metrics, admin endpoints, and worker heartbeat. M9 dashboard UI and full-text log search still unverified. See [[pr-qa/pr-103-system-monitoring-prometheus]].

 ## FRS Gap Closures (May 2026 batch)
 - **M6-G (XAI Narrative Generation)**: ✅ CLOSED — PR #104: `POST /api/analytics/incidents/{id}/narrative`, batch endpoint, `ai_narrative` + `ai_narrative_confidence` columns on `fire_incidents`. Qwen2.5-3B via Ollama.
 - **M6-F (Suricata IDS Integration)**: ✅ CLOSED — PR #105: HIGH severity auto-incident creation, duplicate guard, `security_alert_id` FK, service account pre-provisioned.
 - **M9 (System Monitoring)**: 🟡 PARTIAL — PR #103: Prometheus `/metrics` endpoint + admin-only system/worker monitoring. M9 dashboard UI and full-text log search still gap.
 - **M4 (Incident Workflow)**: ✅ CLOSED — PR #102: AFOR import fixes, field persistence, validator audit trail, VALIDATOR role routing, immutable rule fix.

## Related
- [[concepts/frs-module-map]]
- [[security/security-baseline]]
- [[gaps/ui-ux-gap-register]]
- [[gaps/functional-bug-register]]
