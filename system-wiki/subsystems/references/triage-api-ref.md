---
title: Triage Queue API Reference
created: 2026-05-16
updated: 2026-05-16
type: backend
tags: [wims-bfp, triage, citizen-reports, api-reference, backend]
sources: [src/backend/api/routes/triage.py]
status: draft
---

# Triage Queue — Full API Reference

Complete function-level documentation for `src/backend/api/routes/triage.py` (~222 lines). Covers citizen report promotion workflow accessible by `REGIONAL_ENCODER` and `NATIONAL_VALIDATOR`.

---

## Pydantic Schemas

### `BulkPromoteRequest`

**Fields:**

| Name | Type | Required | Description |
|---|---|---|---|
| report_ids | list[int] | Yes | List of `citizen_reports` primary keys to promote |

**Validators:** None — FastAPI auto-validates JSON array of integers.

---

## Helpers

### `_require_encoder_or_validator`

**Decorators/Route:** N/A — FastAPI dependency function  
**Purpose:** Guard dependency ensuring authenticated user has either `REGIONAL_ENCODER` or `NATIONAL_VALIDATOR` role.

**Parameters:**

| Name | Type | Source | Description |
|---|---|---|---|
| current_user | dict | Depends(get_current_wims_user) | Authenticated user dict |

**Returns:** `dict` — the same `current_user` dict if role check passes

**Errors:** 403 — if role is not REGIONAL_ENCODER or NATIONAL_VALIDATOR. Detail includes the offending role.

**Behavior Notes:** Reads `current_user["role"]`. No DB call — pure middleware guard.

---

## Route Handlers

### `get_pending_reports`

**Route:** `@router.get("/pending")`  
**Prefix:** `/api/triage`  
**Auth:** `Depends(_require_encoder_or_validator)` — REGIONAL_ENCODER or NATIONAL_VALIDATOR only  
**DB Session:** `get_db_with_rls`  
**Purpose:** Return all citizen reports with `status = 'PENDING'`, ordered oldest first. Provides triage queue data.

**Parameters:**

| Name | Type | Source | Description |
|---|---|---|---|
| user | dict | Depends(_require_encoder_or_validator) | Auth guard (not used in logic) |
| db | Session | Depends(get_db_with_rls) | SQLAlchemy session with RLS |

**Returns:** `list[dict]` — each item:

| Key | Type | Description |
|---|---|---|
| report_id | int | Primary key from `citizen_reports` |
| latitude | float | `ST_Y(location::geometry)` |
| longitude | float | `ST_X(location::geometry)` |
| description | str | Defaults to `""` if NULL |
| created_at | str\|None | ISO-format timestamp |
| status | str | Always "PENDING" per WHERE clause |

**Errors:** None implicit (403 via auth guard)

**Behavior Notes:** Uses raw SQL via `sqlalchemy.text()`. Decomposes PostGIS `geometry(Point, 4326)` location column into lat/lon floats. Returns `[]` if no pending reports. RLS applies.

### `promote_report`

**Route:** `@router.post("/{report_id}/promote", status_code=201)`  
**Prefix:** `/api/triage`  
**Auth:** `Depends(_require_encoder_or_validator)`  
**DB Session:** `get_db_with_rls`  
**Purpose:** Promote a single PENDING citizen report into an official fire incident. Two-step atomic transaction: INSERT fire_incident (VERIFIED), UPDATE citizen_report (VERIFIED + link back).

**Parameters:**

| Name | Type | Source | Description |
|---|---|---|---|
| report_id | int | Path | Primary key of the `citizen_reports` row |
| request | Request | Injected | Raw request for audit logging (IP, user-agent) |
| user | dict | Depends | Auth user dict; `user["user_id"]` used as encoder_id |
| db | Session | Depends | SQLAlchemy session with RLS |

**Returns:** `{"report_id": int, "incident_id": int}`

**Errors:**

| Status | Condition |
|---|---|
| 404 | No `citizen_reports` row with the given `report_id` |
| 409 | Report exists but status is not "PENDING" |
| 500 | No `ref_regions` seed data, INSERT RETURNING returned no row, or any other DB error |

**Behavior Notes:**
- Transaction handling: explicit try/except with `db.rollback()` on failure
- HTTPException caught and re-raised after rollback
- Region resolution: always picks first row from `wims.ref_regions` as default
- After first commit: calls `sync_incident_to_analytics(db, incident_id)` followed by second commit
- Audit logging: `log_system_audit` with action `PROMOTE_REPORT` on table `fire_incidents`
- RLS may restrict which reports are visible

### `bulk_promote_reports`

**Route:** `@router.post("/bulk-promote", status_code=201)`  
**Prefix:** `/api/triage`  
**Auth:** `Depends(_require_encoder_or_validator)`  
**DB Session:** `get_db_with_rls`  
**Purpose:** Promote multiple PENDING citizen reports in a single request. Returns separate lists of successes and failures. **Not** all-or-nothing — partial success model.

**Parameters:**

| Name | Type | Source | Description |
|---|---|---|---|
| body | BulkPromoteRequest | Body | Contains `report_ids: list[int]` |
| request | Request | Injected | Accepted but NOT used in function body |
| user | dict | Depends | Auth user dict |
| db | Session | Depends | SQLAlchemy session with RLS |

**Returns:**

| Key | Type | Description |
|---|---|---|
| promoted | list[dict] | Each item: `{"report_id": int, "incident_id": int}` |
| failed | list[int] | Raw `report_id` values for reports that could not be promoted |

**Errors:** 500 if no `ref_regions` seed data (hard failure, checked before any individual promotion)

**Behavior Notes:**
- **Partial success model:** A failure for one report does NOT roll back others that already succeeded
- Failure criteria: not found, wrong status, or any exception during INSERT/UPDATE
- Single `db.commit()` commits ALL successfully promoted reports together
- Analytics sync runs in separate loop after first commit
- No per-item audit logging (unlike single-promote route)
- `request` parameter is dead code — accepted but never referenced
