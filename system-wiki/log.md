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
