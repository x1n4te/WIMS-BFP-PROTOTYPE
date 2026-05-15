# System Wiki Log

Chronological record of system-wiki changes. Append-only.
Format: `## [YYYY-MM-DD] action | subject`

## [2026-05-14] create | System wiki initialized
- Created project-local wiki at `/home/xynate/WIMS-BFP-NEW/LOCAL-WIMS-BFP-PROTOTYPE/system-wiki`.
- Copied 15 user-supplied FRS files from `wiki-dir/` into `raw/frs/`.
- Created initial synthesis pages for architecture, FRS module map, backend routes, frontend routes, database schema, security baseline, agent routing, and gap register.
- Created raw codebase snapshot from live repository structure and route/table scans.
## [2026-05-14] update | FRS sources restored, UI/UX evaluations ingested
- `raw/frs/frs-analyticsandreporting.md` filled: M5 now has full spec (statistical query engine, analytics views, export pipeline).
- `raw/frs/frs-cryptographicsecurity.md` filled: M6 now has full spec (OpenBao key management, AES-256-GCM at-rest, TLS 1.3 in-transit).
- `raw/frs/frs-publicanonymousincidentsubmission.md` filled: M14 now has full spec (zero-trust endpoint, Redis rate limiting, auto region resolution, Pydantic validation).
- `raw/frs/frs-systemmonitoringandhealthdashboard.md` filled: M9 now has full spec (psutil/Docker metrics, 60s refresh, log full-text search, configuration management).
- Gap register updated: "Source Gaps" section removed (sources now populated); M9 System Monitoring and UI/UX gaps added.
- New synthesis pages created: `ui-ux/evaluation-loginpage-keycloaksso.md` and `ui-ux/evaluation-system-admin-hub.md` from user desk-check notes.
- `raw/ui-ux/` directory created as immutable source for future evaluations.
- SCHEMA.md updated: added `ui-ux` to types and `ui-ux`, `hci` to domains taxonomy.
- `index.md` updated: total pages 10 -> 12, added UI/UX Evaluations section, updated Raw Source Captures description.
## [2026-05-14] split | UI/UX gaps separated from FRS codebase gap register
- Created `gaps/ui-ux-gap-register.md` — standalone gap register for UI/UX issues.
- Removed UI/UX section from `gaps/frs-codebase-gap-register.md`; added cross-link.
- `index.md` updated: total pages 12 -> 13, Gaps section now lists both registers separately.
- Updated header in `ui-ux-gap-register.md` to reflect teammate as well as user evaluations.
## [2026-05-14] add | Teammate-reported bugs to UI/UX gap register
- 5 bugs added to `gaps/ui-ux-gap-register.md` (Teammate-Reported Bugs section):
  - System Audit record_id shows "-" on create user actions (M12).
  - First login allows missing First Name, Last Name, device name — Keycloak profile validation not enforced.
  - No username change opportunity on first login — admin expects but no UI exists.
  - Session lifespan too short / fast logout — Keycloak token config issue.
  - No account recovery if TOTP authenticator is deleted — hard lockout, no fallback.
## [2026-05-14] split | Functional bugs moved from UI/UX register to standalone register
- `gaps/functional-bug-register.md` created — holds 5 teammate-reported functional/auth bugs (M12).
- Teammate bugs section removed from `gaps/ui-ux-gap-register.md`; cross-links added in both directions.
- `gaps/frs-codebase-gap-register.md` Related section updated to include `functional-bug-register`.
- `index.md` Gaps section updated: all 3 gap registers now listed separately.
- `log.md` entries updated to reflect split.
## [2026-05-14] add | National analyst dashboard evaluation
- Raw notes added to `raw/ui-ux/evaluation-national-analyst.md`.
- Synthesis created at `ui-ux/evaluation-national-analyst.md` — layout issues (L-01–L-04), filter issues (F-01–F-02), plus FRS/codebase gaps not explicitly raised by user (G-01–G-08).
- Cross-referenced with FRS M5 (Analytics), GitHub issues #84–#89.
- Key findings from FRS not raised by user: Top municipalities view missing (G-01), Average response time by region missing (G-02), P0 CRITICAL data pipeline bug (#84 — verify_incident() no analytics sync).
- Execution order per #89: Phase 0 → Phase 1 → Phase 2/3 (parallel) → Phase 5 → Phase 4.
- Added to `ui-ux-gap-register.md` (National Analyst Dashboard section) and `index.md` (UI/UX Evaluations section).
- SCHEMA.md authority model: "Empty or incomplete FRS source files" rule preserved (applies if future sources are empty).
## [2026-05-14] handoff | Session complete, handoff file created
- AGENTS.md updated: added "System Wiki & Agent Context Routing" section pointing agents to system-wiki/.
- Session handoff created: `sessions/2026-05-14_1605_x1n4te_system-wiki-initialization-uiux-evaluations.md` — full session summary, recommended skills, known conventions, open questions.
- Open items for next session: wiki-dir/ cleanup decision, next desk-check page, groupmate wiki access, GitHub Issues conversion of gap register.
## [2026-05-14] update | National analyst backend slice started
- Added API map entries for `GET /api/analytics/export/{task_id}` and `GET /api/analytics/filter-options`.
- Documented `28_analytics_geography_denorm.sql`: denormalized `municipality_name` / `province_name` on `analytics_incident_facts`, plus export task/file metadata on `analytics_export_log`.
- Updated National Analyst evaluation/gap registers: verification sync remains fixed, export backend is implemented but frontend preview/download UX remains pending, and National Analyst sidebar navigation is fixed.
## [2026-05-14] update | National analyst Phase 5 incident drill-down
- Added backend route-map entries for `GET /api/incidents/analyst-list`, `GET /api/incidents/analyst/{incident_id}`, and `GET /api/incidents/analyst/{incident_id}/wildland`.
- Added frontend route-map entries for `/dashboard/analyst/incidents/[id]` and `/dashboard/analyst/incidents/[id]/wildland`.
- Updated National Analyst evaluation and gap registers: incident list/drawer/detail/wildland drill-down are fixed in code and need browser UI verification; export preview remains pending.
## [2026-05-14] handoff | Phase 5 incident drill-down session
- Created `sessions/2026-05-14_2007_x1n4te_phase5-incident-drilldown-handoff.md` with verification notes, next-session cautions, and suggested skills.
## [2026-05-14] update | National analyst Phase 7 wiki validation
- Updated National Analyst synthesis/gap pages to reflect completed Phase 0-6 code: analytics sync, export infrastructure, geography filters, Recharts charts, incident list/drawer/detail/wildland routes, dashboard export preview/download, CSV/PDF/Excel entry points, side-column heatmap, prominent filter labels, top municipalities, response-time view, and analyst sidebar.
- Updated backend/frontend/database maps with the current analyst dashboard route/API/schema state.
- Left browser UI verification, full backend integration test pass, Celery result retention, export cleanup, seeded wildland examples, and scheduled reports as explicit remaining verification/deferred items.
## [2026-05-15] fix | National analyst incident list 500 and dashboard UX
- Fixed analyst incident list/detail SQL to match the live schema: `ref_barangays` / `analytics_incident_facts.barangay_name` for barangay names, derived casualty severity from casualty counts, `fire_incidents.data_hash` for provenance, and derived analytics sync status from fact presence.
- Added `src/backend/tests/test_analyst_incidents_sql_contract.py` to guard against reintroducing nonexistent analyst-list columns.
- Overhauled `/dashboard/analyst` scanability: summary tiles, grouped filters, clearer apply/reset controls, export preview actions, icon-led panel headers, sticky portrait heatmap, and friendlier incident-list error copy.
- Validation completed: focused backend regression test, Python compile for `api/routes/incidents.py`, frontend analyst Vitest suites, and frontend lint. Broader backend integration suites still hang in this environment and need a non-hanging stack/runner.
## [2026-05-15] fix | Keycloak forgot-password local test config
- Fixed `test_keycloak_password_reset.py` flow execution helper to call Keycloak's reset-credentials executions endpoint by URL-encoded flow alias instead of internal flow ID.
- Configured `src/keycloak/bfp-realm.json` with MailHog SMTP defaults for local password-reset email tests.
- Added a `mailhog` service to `src/docker-compose.yml` exposing SMTP `1025` and web/API `8025`.
- Updated security baseline and functional bug register. Targeted Keycloak tests skip in this sandbox because Keycloak is unreachable here; the running local realm may need Admin API update or container recreate/import to pick up SMTP defaults.
## [2026-05-15] fix | Analyst incident list region schema mismatch
- Container logs showed `/api/incidents/analyst-list` failing with `psycopg2.errors.UndefinedColumn: column r.short_name does not exist`.
- Patched analyst list/detail queries to use `ref_regions.region_code` / `region_name` instead of `short_name`.
- Expanded `src/backend/tests/test_analyst_incidents_sql_contract.py` to guard against `r.short_name` regressions.
- Rebuilt/restarted backend and smoke-checked the patched SQL against local Postgres. Local runtime data has `0` `fire_incidents` and `0` analytics facts, so the dashboard will show no visible incidents until data is seeded/imported and verified.
## [2026-05-15] handoff | National analyst validation and Keycloak fixes
- Created `system-wiki/sessions/2026-05-15_1148_xynate_national-analyst-validation-keycloak-handoff.md`.
- Handoff points the next session toward a docs-driven/grill pass for dedicated National Analyst pages and references existing wiki artifacts instead of duplicating them.
