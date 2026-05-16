# Phase 2 — Modular Incident Export Backend

## Context from Phase 1

Phase 1 delivered the analyst dashboard workflow: sessionStorage-based filter handoff, dedicated `[workflow]` pages, selectable `AnalystIncidentList`, and a Trends granularity expansion. The frontend `ExportPreviewModal` already calls `queueAnalyticsExport` / `downloadAnalyticsExport` against `/analytics/export/{csv|pdf|excel}` endpoints. The Celery tasks exist in `tasks/exports.py` and use `get_export_rows` from `services/analytics_read_model.py`.

## Goal

Extend the export pipeline to support **analyst-specific incident export** — exporting a specific selected incident or a filtered set of incidents — with proper modularity, TDD, and a verifiable done state.

---

## Scope

### Backend (FastAPI + Celery)

**New endpoint: `POST /incidents/analyst/export/{format}`**

- `format`: `csv` | `pdf` | `excel`
- Request body: `{ filters: Record<string,any>, columns: string[], incident_ids?: number[] }`
- `incident_ids` is optional. When provided, the query filters to only those incident IDs (intersection with RLS). When absent, uses `filters` as the full search predicate.
- Authorization: same role guard as `/incidents/analyst-list` (NATIONAL_ANALYST or higher).
- Dispatches a Celery task and returns `{ task_id: string }` identical to the existing analytics export pattern.
- **Modular task naming**: tasks are in `tasks/exports.py` — extend the existing `_export` helper with an `incident_ids` parameter. Do NOT duplicate the writer functions.

**Celery task: `export_analyst_incidents_task`**

- Single task that handles all three formats via a `format` kwarg.
- Runs with the requesting user's RLS context (pass `user_id` as before).
- Uses `get_export_rows` with an added `incident_ids` filter clause.
- Logs to `wims.analytics_export_log` with `export_type = 'analyst'` so it's distinguishable from the generic analytics export log.

**Download endpoint: reuse existing `GET /analytics/export/{task_id}`** — no changes needed, the task returns a file path.

**New service function: `get_analyst_export_rows`** in `services/analytics_read_model.py`

- Signature: `get_analyst_export_rows(db: Session, filters: dict, columns: list[str], incident_ids: list[int] | None) -> list[dict[str,Any]]`
- When `incident_ids` is provided, adds `AND a.incident_id = ANY(:incident_ids)` to the WHERE clause.
- Validates that every ID in `incident_ids` passes RLS (the join with `user_region_facts` already enforces this in the existing `get_export_rows` — confirm this or add an explicit check).
- Column allowlist matches `ALLOWED_EXPORT_COLUMNS` in `tasks/exports.py`.

**Route registration**: add to `api/routes/incidents.py` under the analyst section.

### TDD Tests (mandatory — must all pass)

Place in `src/backend/tests/test_analyst_export.py`.

**Unit tests (no DB needed):**
1. `test_export_columns_allowlist_filtering` — pass a list with invalid column names, verify only valid ones are returned.
2. `test_export_task_dispatched_returns_task_id` — mock Celery, POST to the endpoint, assert `{ task_id: <uuid> }` shape.
3. `test_export_incident_ids_passed_to_task` — mock Celery, POST with `incident_ids=[10,20,30]`, assert those IDs appear in the task kwargs.
4. `test_export_unauthorized_role_rejected` — POST as REGIONAL_VIEWER, assert 403.

**Integration tests (real DB with `conftest.py` fixtures):**
5. `test_export_csv_with_filters_returns_200` — POST valid analyst credentials + filters, assert task_id returned and Celery task completed (use CELERY_TASK_ALWAYS_EAGER or poll).
6. `test_export_with_specific_incident_ids` — seed 3 incidents, export with `incident_ids=[id1, id3]`, verify only 2 rows in result.
7. `test_export_respects_rls` — seed incidents in two regions, verify analyst with region=A cannot export incident in region=B even by ID.
8. `test_export_log_inserted` — after successful export, query `analytics_export_log` and assert `export_type = 'analyst'`, `row_count` matches.

**Test fixtures needed in `conftest.py`** (add if missing):
- `analyst_client` — authenticated FastAPI TestClient as NATIONAL_ANALYST.
- `regional_viewer_client` — authenticated as REGIONAL_VIEWER.
- `seed_analyst_incidents(db_session)` — fixture that inserts 5 incidents into `analytics_incident_facts` with known IDs and regions.

### Verification gate

All of the following must pass before Phase 2 is considered done:

```bash
cd src/backend && pytest -v tests/test_analyst_export.py       # all 8 tests pass
cd src/backend && python -m py_compile api/routes/incidents.py  # no syntax errors
cd src/backend && python -m py_compile tasks/exports.py        # no syntax errors
cd src/backend && python -m py_compile services/analytics_read_model.py  # no syntax errors
```

### Wiki update (after tests pass)

After all tests green, append a session log to `system-wiki/log.md` with:
- What was built (new endpoint, new task, new service function)
- Schema change if any (new column `export_type` in `analytics_export_log`)
- Test count (8 new tests)

---

## Constraints

- Do NOT touch `ExportPreviewModal.tsx` or the frontend `api.ts` export functions — the frontend integration is already wired.
- Do NOT create new Celery writer functions — reuse `_write_csv`, `_write_xlsx`, `_write_pdf` from `tasks/exports.py`.
- Do NOT change the existing `/analytics/export/{csv|pdf|excel}` routes — Phase 2 is a separate, parallel export path.
- Keep `incident_ids` validation defensive: empty list is fine (falls back to filters-only), duplicate IDs are deduplicated.
- Maximum 3 files changed/created outside tests: `api/routes/incidents.py`, `tasks/exports.py`, `services/analytics_read_model.py`.