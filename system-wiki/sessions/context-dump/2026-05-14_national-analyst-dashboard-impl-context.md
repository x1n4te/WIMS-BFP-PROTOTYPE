# National Analyst Dashboard — Phase 6 Context Dump
**Created:** 2026-05-14
**Phase:** 6 (Export UX + Heatmap Layout Fix)
**Source:** Phase 5 handoff review + code cross-reference

---

## What Phase 5 Completed

### Backend (Done)
- `GET /api/incidents/analyst-list` — paginated, sortable, VERIFIED-only, analyst/admin RBAC
- `GET /api/incidents/analyst/{incident_id}` — read-only detail, has_wildland_afor flag, provenance fields
- `GET /api/incidents/analyst/{incident_id}/wildland` — wildland AFOR data (alarm statuses + assistance rows)
- `GET /api/analytics/filter-options?field=province|municipality` — cascading geography options
- `GET /api/analytics/export/{task_id}` — download completed Celery export file
- `POST /api/analytics/export/csv|pdf|excel` — dispatch Celery export task (returns task_id)
- `tasks/exports.py` — real CSV/PDF/XLSX writers using reportlab + openpyxl; logs to analytics_export_log
- `analytics_read_model.py` — sync_incident_to_analytics, sync_incidents_batch, backfill_analytics_facts all include municipality_name + province_name from incident_nonsensitive_details.city_municipality / province_district
- `28_analytics_geography_denorm.sql` — idempotent migration adding municipality_name/province_name columns + indexes to analytics_incident_facts

### Frontend (Done)
- `AnalystIncidentList.tsx` — 25 rows/page, sortable headers, 640px drawer, full-page link
- `/dashboard/analyst/incidents/[id]/page.tsx` — read-only, no edit/validator controls
- `/dashboard/analyst/incidents/[id]/wildland/page.tsx` — wildland-specific fields
- Recharts: TypeDistributionChart (donut), TopBarangaysChart (horizontal bar), ResponseTimeChart (bar w/ avg/min/max)
- Filter bar: region → province → municipality cascade, date range, incident type, alarm level, casualty severity, damage min/max
- Sidebar: NATIONAL_ANALYST section pointing to /dashboard/analyst and /profile

### Verification
- `python -m py_compile` on incidents.py + analytics_read_model.py — passed
- `git diff --check` — passed
- `vitest run` (3 test files) — 59 tests passed
- `npm run lint` — passed (3 pre-existing warnings)
- `tsc --noEmit` — fails on pre-existing admin/login/offline-sync type debt (not phase-5 blocking)

---

## What Phase 6 Must Implement

### 1. Export UX (CRITICAL — currently broken)

**Current state:** `analyst/page.tsx:687-717` uses raw inline `fetch` directly to `/api/analytics/export/pdf` and `/api/analytics/export/excel` with hardcoded empty `filters: {}`. On response, shows `alert('PDF export queued: ' + task_id)`. No download, no preview, no column selection.

**What needs building:**
- Add to `src/frontend/src/lib/api.ts`:
  - `queueExport(format: 'csv'|'pdf'|'excel', filters, columns) → { task_id: string }`
  - `pollExportDownload(task_id) → { state: 'PENDING'|'SUCCESS'|'FAILURE', path?: string }`
  - Or better: `downloadExport(task_id: string)` — calls `GET /api/analytics/export/{task_id}`, extracts filename from Content-Disposition, triggers browser download
- Replace inline fetch in `analyst/page.tsx` with proper state machine:
  - `idle | queued | polling | downloading | done | error`
  - After queueing, poll via `pollExportDownload` until state != PENDING
  - On SUCCESS, call `downloadExport` to trigger browser download
- Export preview component (new, not existing):
  - Modal/sidebar showing: active filters summary, column checkboxes (from DEFAULT_EXPORT_COLUMNS), estimated row count (call `count_export_rows` or pass count from list)
  - "Queue Export" button fires the actual task

### 2. Heatmap Layout Fix

**Current state:** Heatmap is full-width (`card` with `card-body p-0`) in a single-column stack.
**Spec:** "tall/portrait and side-positioned on desktop" — side column on desktop.
**What needs building:** CSS grid re-layout of the main dashboard content area. On desktop (`lg:`), heatmap should be portrait/tall and occupy a side column (~300-400px wide) while charts/list occupy the main column. Mobile: stacked as-is.

### 3. Filter Bar Prominence

**Current state:** Filter labels are `text-[11px]`, inputs are `text-sm`.
**Spec:** "Filters should be larger and more prominent than 'All Synced' badge" (which no longer exists — was removed).
**What needs building:** Increase label font size to `text-sm` or `text-base`, increase input height/padding. Possibly reduce the number of filters shown in the initial row (move comparative period filters into a collapsible "Advanced" section).

### 4. (No work needed)
- Incident list, detail, wildland routes — done
- Recharts charts — done
- Filter cascade logic — done
- Analytics sync — done
- Backend export tasks — done

---

## Key Code Locations

| File | Purpose |
|---|---|
| `src/backend/api/routes/analytics.py` | Export dispatch + download endpoints |
| `src/backend/api/routes/incidents.py:577-877` | Analyst incident list/detail/wildland |
| `src/backend/tasks/exports.py` | CSV/PDF/XLSX Celery tasks, _insert_export_log |
| `src/backend/services/analytics_read_model.py` | get_export_rows, get_filter_options, sync_incident_to_analytics |
| `src/frontend/src/app/dashboard/analyst/page.tsx` | Dashboard page — export buttons at lines 687-717 |
| `src/frontend/src/components/analytics/AnalystIncidentList.tsx` | Incident list + drawer |
| `src/frontend/src/lib/api.ts` | API helpers — add queueExport/pollExportDownload/downloadExport here |
| `src/frontend/src/components/analytics/HeatmapViewer.tsx` | Map component (loaded dynamically, ssr:false) |

---

## API Contract for Export Flow

```
POST /api/analytics/export/csv  Body: { filters: {}, columns: [] }  → { task_id: string }
POST /api/analytics/export/pdf  → { task_id: string }
POST /api/analytics/export/excel  → { task_id: string }
GET  /api/analytics/export/{task_id}  → FileResponse (csv/pdf/xlsx) or 409 if pending/failed
```

Frontend must:
1. POST to queue → get task_id
2. Poll GET /api/analytics/export/{task_id} until file is ready (or use client-side polling with setInterval)
3. On success, trigger browser download (window.location or anchor click)

---

## Gaps Status

| Gap | Status for Phase 6 |
|---|---|
| Export backend (CSV/PDF/XLSX) | ✅ Done — frontend UX missing |
| Export preview container | ❌ Needs implementation |
| Heatmap aspect ratio + position | ❌ Needs implementation |
| Filter bar prominence/sizing | ❌ Needs implementation |
| Top municipalities view | ✅ Done via Top-N dimension=municipality |
| Response time by region | ✅ Done |
| Analyst sidebar | ✅ Done |
| Incident detail/wildland pages | ✅ Done |

---

## Pre-existing Issues (Not Phase 6 Scope)

- `tsc --noEmit` fails on admin/login/offline-sync type debt
- `npm run lint` 3 pre-existing warnings
- Scheduled reports deferred per plan
- M9 system monitoring not yet implemented