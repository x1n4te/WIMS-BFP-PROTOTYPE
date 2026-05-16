import hashlib
import json
import logging
import os
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
from auth import get_current_wims_user, get_analyst_or_admin
from database import get_db_with_rls
from schemas.incident import IncidentCreate, IncidentResponse
from services.analytics_read_model import sync_incident_to_analytics
from tasks.exports import export_analyst_incidents_task
from api.routes.regional import _normalize_general_category

router = APIRouter(prefix="/api", tags=["incidents"])
logger = logging.getLogger("wims.incidents")

STORAGE_DIR = "/app/storage/attachments"


def _resolve_storage_dir() -> str:
    """Pick the first writable attachment directory."""
    candidates = [
        os.getenv("WIMS_ATTACHMENT_STORAGE_DIR", "").strip(),
        STORAGE_DIR,
        "/tmp/wims/attachments",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            os.makedirs(candidate, exist_ok=True)
            test_path = os.path.join(candidate, ".write_test")
            with open(test_path, "wb") as fp:
                fp.write(b"ok")
            os.remove(test_path)
            return candidate
        except Exception:
            continue
    raise HTTPException(status_code=500, detail="No writable attachment storage path available")


@router.post("/incidents/upload-bundle")
def upload_incident_bundle(
    body: Annotated[dict[str, Any], Body(...)],
    user: Annotated[dict, Depends(get_current_wims_user)],
    db: Annotated[Session, Depends(get_db_with_rls)],
):
    """Compatibility endpoint used by existing frontend bundle submit flow."""
    incidents = body.get("incidents")
    if not isinstance(incidents, list) or len(incidents) == 0:
        raise HTTPException(status_code=400, detail="No incidents provided")

    user_id = user["user_id"]
    user_role = user.get("role", "")

    # Resolve the user's assigned region from the DB (not available in the base JWT payload)
    assigned_row = db.execute(
        text("SELECT assigned_region_id FROM wims.users WHERE user_id = CAST(:uid AS uuid)"),
        {"uid": user_id},
    ).fetchone()
    assigned_region_id = assigned_row[0] if assigned_row else None

    region_id_raw = body.get("region_id")
    try:
        region_id = int(region_id_raw)
    except (TypeError, ValueError):
        # Fall back to assigned region (encoder) or first available region
        if assigned_region_id:
            region_id = int(assigned_region_id)
        else:
            region_row = db.execute(
                text("SELECT region_id FROM wims.ref_regions LIMIT 1")
            ).fetchone()
            if not region_row:
                raise HTTPException(status_code=500, detail="No region available")
            region_id = int(region_row[0])

    # Enforce REGIONAL_ENCODER can only submit for their assigned region
    if user_role in ("REGIONAL_ENCODER", "ENCODER") and assigned_region_id is not None:
        if region_id != int(assigned_region_id):
            raise HTTPException(
                status_code=403,
                detail="REGION_MISMATCH: You can only submit incidents for your assigned region.",
            )

    batch_row = db.execute(
        text(
            """
            INSERT INTO wims.data_import_batches (region_id, uploaded_by, record_count)
            VALUES (:region_id, CAST(:uid AS uuid), :count)
            RETURNING batch_id
            """
        ),
        {"region_id": region_id, "uid": user_id, "count": len(incidents)},
    ).fetchone()

    if not batch_row:
        raise HTTPException(status_code=500, detail="Failed to create import batch")

    batch_id = int(batch_row[0])
    incident_ids: list[int] = []

    def _safe_int(v: Any, default: int = 0) -> int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    def _safe_float(v: Any, default: float = 0.0) -> float:
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    for item in incidents:
        if not isinstance(item, dict):
            continue

        ns = item.get("incident_nonsensitive_details") or {}
        sens = item.get("incident_sensitive_details") or {}
        if not isinstance(ns, dict):
            ns = {}
        if not isinstance(sens, dict):
            sens = {}

        lon = _safe_float(item.get("longitude"), 0.0)
        lat = _safe_float(item.get("latitude"), 0.0)

        incident_type_code_val = (ns.get("incident_type_code") or "").strip().upper() or None
        station_code_val = (ns.get("station_code") or "TBA").strip() or "TBA"

        city_id: int | None = None
        city_id_raw = ns.get("city_id")
        try:
            city_candidate = int(city_id_raw) if city_id_raw is not None else None
        except (TypeError, ValueError):
            city_candidate = None
        if city_candidate and city_candidate > 0:
            city_exists = db.execute(
                text("SELECT 1 FROM wims.ref_cities WHERE city_id = :cid LIMIT 1"),
                {"cid": city_candidate},
            ).fetchone()
            city_id = city_candidate if city_exists else None

        inc_row = db.execute(
            text(
                """
                INSERT INTO wims.fire_incidents
                    (import_batch_id, encoder_id, region_id, location, verification_status,
                     incident_type_code, reference_number)
                VALUES
                    (:batch_id, CAST(:uid AS uuid), :region_id,
                     ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                     'DRAFT', :incident_type_code, NULL)
                RETURNING incident_id
                """
            ),
            {
                "batch_id": batch_id,
                "uid": user_id,
                "region_id": region_id,
                "lon": lon,
                "lat": lat,
                "incident_type_code": incident_type_code_val,
            },
        ).fetchone()

        if not inc_row:
            continue

        incident_id = int(inc_row[0])
        incident_ids.append(incident_id)

        db.execute(
            text(
                """
                INSERT INTO wims.incident_nonsensitive_details (
                    incident_id, city_id,
                    notification_dt, alarm_level, general_category, sub_category,
                    responder_type, fire_origin, extent_of_damage,
                    structures_affected, households_affected, families_affected,
                    individuals_affected, vehicles_affected,
                    total_response_time_minutes, total_gas_consumed_liters,
                    resources_deployed, alarm_timeline, problems_encountered,
                    recommendations, fire_station_name, stage_of_fire,
                    extent_total_floor_area_sqm, extent_total_land_area_hectares,
                    distance_from_station_km, station_code,
                    city_municipality, province_district
                ) VALUES (
                    :incident_id, :city_id,
                    CAST(:notification_dt AS timestamptz), :alarm_level, :general_category, :sub_category,
                    :responder_type, :fire_origin, :extent_of_damage,
                    :structures_affected, :households_affected, :families_affected,
                    :individuals_affected, :vehicles_affected,
                    :total_response_time_minutes, :total_gas_consumed_liters,
                    CAST(:resources_deployed AS jsonb), CAST(:alarm_timeline AS jsonb), CAST(:problems_encountered AS jsonb),
                    :recommendations, :fire_station_name, :stage_of_fire,
                    :floor_area, :land_area,
                    :distance_from_station_km, :station_code,
                    :city_municipality, :province_district
                )
                """
            ),
            {
                "incident_id": incident_id,
                "city_id": city_id,
                "notification_dt": ns.get("notification_dt"),
                "alarm_level": ns.get("alarm_level", ""),
                "general_category": _normalize_general_category(
                    ns.get("general_category", "") or ""
                ),
                "sub_category": ns.get("incident_type") or ns.get("sub_category") or "",
                "responder_type": ns.get("responder_type", ""),
                "fire_origin": ns.get("fire_origin", ""),
                "extent_of_damage": ns.get("extent_of_damage", ""),
                "structures_affected": _safe_int(ns.get("structures_affected")),
                "households_affected": _safe_int(ns.get("households_affected")),
                "families_affected": _safe_int(ns.get("families_affected")),
                "individuals_affected": _safe_int(ns.get("individuals_affected")),
                "vehicles_affected": _safe_int(ns.get("vehicles_affected")),
                "total_response_time_minutes": _safe_int(ns.get("total_response_time_minutes")),
                "total_gas_consumed_liters": _safe_float(ns.get("total_gas_consumed_liters")),
                "resources_deployed": json.dumps(ns.get("resources_deployed", {})),
                "alarm_timeline": json.dumps(ns.get("alarm_timeline", {})),
                "problems_encountered": json.dumps(ns.get("problems_encountered", [])),
                "recommendations": ns.get("recommendations", ""),
                "fire_station_name": ns.get("fire_station_name", ""),
                "stage_of_fire": ns.get("stage_of_fire", ""),
                "floor_area": _safe_float(ns.get("extent_total_floor_area_sqm")),
                "land_area": _safe_float(ns.get("extent_total_land_area_hectares")),
                "distance_from_station_km": _safe_float(
                    ns.get("distance_to_fire_scene_km") or ns.get("distance_from_station_km")
                ),
                "station_code": station_code_val,
                "city_municipality": ns.get("city_municipality") or "",
                "province_district": ns.get("province_district") or "",
            },
        )

        db.execute(
            text(
                """
                INSERT INTO wims.incident_sensitive_details (
                    incident_id, street_address, landmark,
                    caller_name, caller_number, receiver_name,
                    owner_name, establishment_name,
                    narrative_report, disposition,
                    disposition_prepared_by, disposition_noted_by,
                    personnel_on_duty, other_personnel, casualty_details,
                    is_icp_present, icp_location
                ) VALUES (
                    :incident_id, :street_address, :landmark,
                    :caller_name, :caller_number, :receiver_name,
                    :owner_name, :establishment_name,
                    :narrative_report, :disposition,
                    :disposition_prepared_by, :disposition_noted_by,
                    CAST(:personnel_on_duty AS jsonb), CAST(:other_personnel AS jsonb), CAST(:casualty_details AS jsonb),
                    :is_icp_present, :icp_location
                )
                """
            ),
            {
                "incident_id": incident_id,
                "street_address": sens.get("street_address") or ns.get("incident_address") or "",
                "landmark": sens.get("landmark") or ns.get("nearest_landmark") or "",
                "caller_name": sens.get("caller_name", ""),
                "caller_number": sens.get("caller_number", ""),
                "receiver_name": sens.get("receiver_name", ""),
                "owner_name": sens.get("owner_name", ""),
                "establishment_name": sens.get("establishment_name", ""),
                "narrative_report": sens.get("narrative_report", ""),
                "disposition": sens.get("disposition", ""),
                "disposition_prepared_by": sens.get("prepared_by_officer")
                or sens.get("disposition_prepared_by", ""),
                "disposition_noted_by": sens.get("noted_by_officer")
                or sens.get("disposition_noted_by", ""),
                "personnel_on_duty": json.dumps(sens.get("personnel_on_duty", {})),
                "other_personnel": json.dumps(ns.get("other_personnel", [])),
                "casualty_details": json.dumps(sens.get("casualty_details", {})),
                "is_icp_present": bool(sens.get("is_icp_present", False)),
                "icp_location": sens.get("icp_location", ""),
            },
        )

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("upload-bundle commit failed")
        raise HTTPException(
            status_code=500, detail=f"upload-bundle commit failed: {type(e).__name__}"
        ) from None

    for iid in incident_ids:
        try:
            sync_incident_to_analytics(db, iid)
        except Exception:
            logger.warning("Failed to sync incident %s to analytics read model", iid)
    db.commit()

    return {
        "status": "ok",
        "batch_id": batch_id,
        "incident_ids": incident_ids,
        "message": f"Committed {len(incident_ids)} incident(s).",
    }


@router.post("/incidents/{incident_id}/attachments", status_code=201)
async def upload_attachment(
    incident_id: int,
    file: UploadFile = File(...),
    db: Annotated[Session, Depends(get_db_with_rls)] = None,
    user: Annotated[dict, Depends(get_current_wims_user)] = None,
):
    """
    Upload an attachment (e.g., photo sketch) for a specific incident.
    Saves to disk and records in wims.incident_attachments.
    """
    storage_dir = _resolve_storage_dir()

    # 1. Verify incident exists and belongs to user's region (standard isolation)
    # For now, just check existence
    incident = db.execute(
        text("SELECT incident_id FROM wims.fire_incidents WHERE incident_id = :iid"),
        {"iid": incident_id},
    ).fetchone()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # 2. Save file to disk
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = os.path.join(storage_dir, unique_filename)

    sha256_hash = hashlib.sha256()
    try:
        with open(storage_path, "wb") as buffer:
            while content := await file.read(1024 * 1024):  # Read in chunks
                sha256_hash.update(content)
                buffer.write(content)
    except Exception:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # 3. Record in DB
    try:
        db.execute(
            text("""
                INSERT INTO wims.incident_attachments (
                    incident_id, file_name, storage_path, mime_type, file_hash_sha256, uploaded_by
                ) VALUES (
                    :iid, :fname, :path, :mime, :hash, :uid
                )
            """),
            {
                "iid": incident_id,
                "fname": file.filename,
                "path": storage_path,
                "mime": file.content_type,
                "hash": sha256_hash.hexdigest(),
                "uid": user["user_id"],
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        if os.path.exists(storage_path):
            os.remove(storage_path)
        logger.exception("Database error during attachment upload")
        raise HTTPException(status_code=500, detail="Internal server error")

    return {
        "status": "ok",
        "attachment_id": incident_id,  # Serial ID, but we don't have it immediately without RETURNING
        "message": "Attachment uploaded successfully",
    }


@router.post("/incidents", response_model=IncidentResponse, status_code=201)
def create_incident(
    body: IncidentCreate,
    user: Annotated[dict, Depends(get_current_wims_user)],
    db: Annotated[Session, Depends(get_db_with_rls)],
) -> IncidentResponse:
    """
    Create a fire incident from geospatial intake.
    Requires authenticated Keycloak user present in wims.users.
    """
    wkt = f"SRID=4326;POINT({body.longitude} {body.latitude})"
    user_id = user["user_id"]

    # Resolve a default region (required by schema)
    region_row = db.execute(text("SELECT region_id FROM wims.ref_regions LIMIT 1")).fetchone()
    if region_row is None:
        raise HTTPException(
            status_code=500, detail="No ref_regions seed data — cannot create incident"
        )

    region_id = region_row[0]

    result = db.execute(
        text("""
            INSERT INTO wims.fire_incidents (region_id, encoder_id, location, verification_status)
            VALUES (:region_id, :encoder_id, ST_GeogFromText(:wkt), :verification_status)
            RETURNING incident_id, location, encoder_id, verification_status, created_at
        """),
        {
            "region_id": region_id,
            "encoder_id": user_id,
            "wkt": wkt,
            "verification_status": body.verification_status,
        },
    )
    row = result.fetchone()
    db.commit()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create incident")

    incident_id = row[0]
    sync_incident_to_analytics(db, incident_id)
    db.commit()

    # Extract lat/lon from PostGIS geography for response
    coord_row = db.execute(
        text(
            "SELECT ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lon FROM wims.fire_incidents WHERE incident_id = :iid"
        ),
        {"iid": incident_id},
    ).fetchone()

    lat = float(coord_row[0])
    lon = float(coord_row[1])

    return IncidentResponse(
        incident_id=incident_id,
        latitude=lat,
        longitude=lon,
        encoder_id=row[2],
        status=row[3],
        created_at=row[4],
    )


@router.get("/incidents")
def get_incidents(
    user: Annotated[dict, Depends(auth.get_incident_viewer)],
    db: Annotated[Session, Depends(get_db_with_rls)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    Fetch fire incidents. Scoped to region if user has one, otherwise national.
    """
    region_id = user.get("assigned_region_id")

    where_clauses = ["fi.is_archived = FALSE"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if region_id is not None:
        where_clauses.append("fi.region_id = :region_id")
        params["region_id"] = region_id

    if category:
        where_clauses.append("nd.general_category = :category")
        params["category"] = category
    if status:
        where_clauses.append("fi.verification_status = :status")
        params["status"] = status

    where_sql = " AND ".join(where_clauses)

    rows = db.execute(
        text(
            f"""
            SELECT fi.incident_id, fi.verification_status, fi.created_at,
                   nd.notification_dt, nd.general_category, nd.alarm_level,
                   nd.fire_station_name, nd.structures_affected,
                   nd.households_affected, nd.individuals_affected,
                   nd.responder_type, nd.fire_origin, nd.extent_of_damage,
                   sd.owner_name, sd.establishment_name, sd.caller_name,
                   rb.barangay_name, nd.specific_type
            FROM wims.fire_incidents fi
            LEFT JOIN wims.incident_nonsensitive_details nd ON nd.incident_id = fi.incident_id
            LEFT JOIN wims.incident_sensitive_details sd ON sd.incident_id = fi.incident_id
            LEFT JOIN wims.ref_barangays rb ON rb.barangay_id = nd.barangay_id
            WHERE {where_sql}
            ORDER BY fi.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        ),
        params,
    ).fetchall()

    total = (
        db.execute(
            text(
                f"""
            SELECT COUNT(*) FROM wims.fire_incidents fi
            LEFT JOIN wims.incident_nonsensitive_details nd ON nd.incident_id = fi.incident_id
            WHERE {where_sql}
        """
            ),
            {k: v for k, v in params.items() if k not in ("limit", "offset")},
        ).scalar()
        or 0
    )

    return {
        "items": [
            {
                "incident_id": r[0],
                "verification_status": r[1],
                "created_at": r[2].isoformat() if r[2] else None,
                "notification_dt": r[3].isoformat() if r[3] else None,
                "general_category": r[4],
                "alarm_level": r[5],
                "fire_station_name": r[6],
                "structures_affected": r[7],
                "households_affected": r[8],
                "individuals_affected": r[9],
                "responder_type": r[10],
                "fire_origin": r[11],
                "extent_of_damage": r[12],
                "owner_name": r[13],
                "establishment_name": r[14],
                "caller_name": r[15],
                "barangay": r[16],
                "specific_type": r[17],
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# -----------------------------------------------------------------------
# National Analyst — Incident List (p5a)
# -----------------------------------------------------------------------
ANALYST_LIST_SORT_COLUMNS = {
    "notification_dt",
    "region",
    "municipality_name",
    "barangay_name",
    "general_category",
    "sub_category",
    "alarm_level",
    "estimated_damage_php",
    "total_response_time_minutes",
}


class AnalystIncidentExportRequest(BaseModel):
    filters: dict[str, Any] = {}
    columns: list[str] = []
    incident_ids: Optional[list[int]] = None


def _append_analyst_casualty_filter(
    where_clauses: list[str],
    casualty_severity: str,
) -> None:
    casualty_columns = {
        "civilian_injured": "COALESCE(aif.civilian_injured, nd.civilian_injured, 0)",
        "civilian_deaths": "COALESCE(aif.civilian_deaths, nd.civilian_deaths, 0)",
        "firefighter_injured": "COALESCE(aif.firefighter_injured, nd.firefighter_injured, 0)",
        "firefighter_deaths": "COALESCE(aif.firefighter_deaths, nd.firefighter_deaths, 0)",
    }
    deaths = f"({casualty_columns['civilian_deaths']} + {casualty_columns['firefighter_deaths']})"
    injuries = f"({casualty_columns['civilian_injured']} + {casualty_columns['firefighter_injured']})"

    if casualty_severity == "high":
        where_clauses.append(f"{deaths} > 0")
    elif casualty_severity == "medium":
        where_clauses.append(f"{injuries} > 0 AND {deaths} = 0")
    elif casualty_severity == "low":
        where_clauses.append(f"{injuries} = 0 AND {deaths} = 0")


def _analyst_json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _analyst_row_dict(row: Any) -> dict[str, Any]:
    return {key: _analyst_json_value(value) for key, value in row._mapping.items()}


@router.post("/incidents/analyst/export/{export_format}")
def export_analyst_incidents(
    export_format: str,
    body: AnalystIncidentExportRequest,
    current_user: Annotated[dict, Depends(get_analyst_or_admin)],
):
    """Queue analyst incident export for selected IDs or the supplied filters."""
    if export_format not in {"csv", "pdf", "excel"}:
        raise HTTPException(status_code=422, detail="format must be csv, pdf, or excel")

    incident_ids = sorted(set(body.incident_ids or [])) or None
    result = export_analyst_incidents_task.delay(
        user_id=str(current_user["user_id"]),
        filters=body.filters,
        columns=body.columns,
        incident_ids=incident_ids,
        format=export_format,
    )
    return {"task_id": result.id}


@router.get("/incidents/analyst-list")
def get_analyst_incident_list(
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    province: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    alarm_level: Optional[str] = Query(None),
    casualty_severity: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    damage_min: Optional[float] = Query(None, ge=0),
    damage_max: Optional[float] = Query(None, ge=0),
    incident_ids: Optional[str] = Query(None, description="Comma-separated incident IDs"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query(None, pattern="^(asc|desc)$"),
):
    """
    National Analyst incident list — verified incidents only.

    Requires: NATIONAL_ANALYST or SYSTEM_ADMIN.
    Always filters: verification_status = 'VERIFIED', is_archived = FALSE.
    """
    sort_by_col = sort_by if sort_by and sort_by in ANALYST_LIST_SORT_COLUMNS else "notification_dt"
    sort_dir_val = sort_dir if sort_dir in ("asc", "desc") else "desc"

    where_clauses = ["fi.verification_status = 'VERIFIED'", "fi.is_archived = FALSE"]
    params: dict[str, Any] = {}

    if start_date:
        where_clauses.append("nd.notification_dt >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("nd.notification_dt <= :end_date")
        params["end_date"] = end_date
    if region_id:
        where_clauses.append("fi.region_id = :region_id")
        params["region_id"] = region_id
    if province:
        where_clauses.append("aif.province_name = :province")
        params["province"] = province
    if municipality:
        where_clauses.append("aif.municipality_name = :municipality")
        params["municipality"] = municipality
    if incident_type:
        where_clauses.append("nd.general_category = :incident_type")
        params["incident_type"] = incident_type
    if alarm_level:
        where_clauses.append("nd.alarm_level = :alarm_level")
        params["alarm_level"] = alarm_level

    if incident_ids:
        try:
            parsed_incident_ids = [int(x.strip()) for x in incident_ids.split(",") if x.strip()]
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="incident_ids must be comma-separated integers") from exc
        if parsed_incident_ids:
            where_clauses.append("fi.incident_id = ANY(:incident_ids)")
            params["incident_ids"] = parsed_incident_ids

    if casualty_severity:
        _append_analyst_casualty_filter(where_clauses, casualty_severity)

    if damage_min is not None:
        where_clauses.append("COALESCE(aif.estimated_damage_php, nd.estimated_damage_php, 0) >= :damage_min")
        params["damage_min"] = damage_min
    if damage_max is not None:
        where_clauses.append("COALESCE(aif.estimated_damage_php, nd.estimated_damage_php, 0) <= :damage_max")
        params["damage_max"] = damage_max

    where_sql = " AND ".join(where_clauses)

    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    order_sql = f"ORDER BY {sort_by_col} {'ASC' if sort_dir_val == 'asc' else 'DESC'}"

    list_sql = f"""
        SELECT
            fi.incident_id,
            nd.notification_dt,
            COALESCE(aif.province_name, '')             AS province_name,
            COALESCE(aif.municipality_name, '')         AS municipality_name,
            COALESCE(aif.barangay_name, rb.barangay_name, '') AS barangay_name,
            COALESCE(nd.general_category, '')           AS general_category,
            COALESCE(nd.sub_category, '')              AS sub_category,
            COALESCE(nd.alarm_level, '')               AS alarm_level,
            COALESCE(aif.estimated_damage_php, nd.estimated_damage_php) AS estimated_damage_php,
            COALESCE(aif.total_response_time_minutes, nd.total_response_time_minutes) AS total_response_time_minutes,
            COALESCE(r.region_code, r.region_name, '') AS region,
            fi.verification_status,
            fi.reference_number,
            fi.created_at
        FROM wims.fire_incidents fi
        LEFT JOIN wims.incident_nonsensitive_details nd  ON nd.incident_id = fi.incident_id
        LEFT JOIN wims.analytics_incident_facts aif       ON aif.incident_id = fi.incident_id
        LEFT JOIN wims.ref_regions r                      ON r.region_id = fi.region_id
        LEFT JOIN wims.ref_barangays rb                   ON rb.barangay_id = nd.barangay_id
        WHERE {where_sql}
        {order_sql}
        LIMIT :limit OFFSET :offset
    """
    params["sort_by"] = sort_by_col
    params["sort_dir"] = sort_dir_val

    rows = db.execute(text(list_sql), params).fetchall()

    # Count
    count_sql = f"""
        SELECT COUNT(*)
        FROM wims.fire_incidents fi
        LEFT JOIN wims.incident_nonsensitive_details nd  ON nd.incident_id = fi.incident_id
        LEFT JOIN wims.analytics_incident_facts aif     ON aif.incident_id = fi.incident_id
        LEFT JOIN wims.ref_barangays rb                 ON rb.barangay_id = nd.barangay_id
        WHERE {where_sql}
    """
    total = db.execute(
        text(count_sql),
        {k: v for k, v in params.items() if k not in ("limit", "offset", "sort_by", "sort_dir")},
    ).scalar() or 0

    return {
        "incidents": [
            {
                "incident_id": r[0],
                "notification_dt": r[1].isoformat() if r[1] else None,
                "province_name": r[2],
                "municipality_name": r[3],
                "barangay_name": r[4],
                "general_category": r[5],
                "sub_category": r[6],
                "alarm_level": r[7],
                "estimated_damage_php": float(r[8]) if r[8] is not None else None,
                "total_response_time_minutes": r[9],
                "region": r[10],
                "verification_status": r[11],
                "reference_number": r[12],
                "created_at": r[13].isoformat() if r[13] else None,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# -----------------------------------------------------------------------
# National Analyst — Incident Detail (p5e)
# -----------------------------------------------------------------------
@router.get("/incidents/analyst/{incident_id}")
def get_analyst_incident_detail(
    incident_id: int,
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
):
    """
    National Analyst detail for a single incident.

    Requires: NATIONAL_ANALYST or SYSTEM_ADMIN.
    Returns 404 if the incident is not VERIFIED or is archived.
    Includes provenance fields and has_wildland_afor flag.
    """
    row = db.execute(
        text("""
            SELECT
                fi.incident_id,
                fi.reference_number,
                fi.encoder_id,
                fi.verification_status,
                fi.is_archived,
                fi.created_at,
                fi.data_hash,
                nd.notification_dt,
                COALESCE(r.region_code, r.region_name, '') AS region,
                COALESCE(aif.province_name, '')     AS province_name,
                COALESCE(aif.municipality_name, '')  AS municipality_name,
                COALESCE(aif.barangay_name, rb.barangay_name, '') AS barangay_name,
                COALESCE(nd.general_category, '')    AS general_category,
                COALESCE(nd.sub_category, '')       AS sub_category,
                COALESCE(nd.alarm_level, '')        AS alarm_level,
                COALESCE(aif.estimated_damage_php, nd.estimated_damage_php) AS estimated_damage_php,
                COALESCE(aif.total_response_time_minutes, nd.total_response_time_minutes) AS total_response_time_minutes,
                CASE
                    WHEN (COALESCE(aif.civilian_deaths, nd.civilian_deaths, 0) + COALESCE(aif.firefighter_deaths, nd.firefighter_deaths, 0)) > 0 THEN 'high'
                    WHEN (COALESCE(aif.civilian_injured, nd.civilian_injured, 0) + COALESCE(aif.firefighter_injured, nd.firefighter_injured, 0)) > 0 THEN 'medium'
                    ELSE 'low'
                END AS casualty_severity,
                CASE WHEN aif.incident_id IS NULL THEN 'MISSING' ELSE 'SYNCED' END AS sync_status
            FROM wims.fire_incidents fi
            LEFT JOIN wims.incident_nonsensitive_details nd  ON nd.incident_id = fi.incident_id
            LEFT JOIN wims.analytics_incident_facts aif       ON aif.incident_id = fi.incident_id
            LEFT JOIN wims.ref_regions r                      ON r.region_id = fi.region_id
            LEFT JOIN wims.ref_barangays rb                   ON rb.barangay_id = nd.barangay_id
            WHERE fi.incident_id = :iid
        """),
        {"iid": incident_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Fail if not VERIFIED or is archived
    if row[4]:  # is_archived
        raise HTTPException(status_code=404, detail="Incident not found")
    if row[3] != "VERIFIED":  # verification_status
        raise HTTPException(status_code=404, detail="Incident not found")

    # Check wildland AFOR existence
    wildland_row = db.execute(
        text("SELECT 1 FROM wims.incident_wildland_afor WHERE incident_id = :iid LIMIT 1"),
        {"iid": incident_id},
    ).fetchone()
    has_wildland_afor = wildland_row is not None

    # Encoder username (from users table)
    encoder_row = db.execute(
        text("SELECT username FROM wims.users WHERE user_id = CAST(:uid AS uuid)"),
        {"uid": str(row[2])},
    ).fetchone()
    encoder_username = encoder_row[0] if encoder_row else None

    return {
        "incident_id": row[0],
        "reference_number": row[1],
        "encoder_id": str(row[2]),
        "encoder_username": encoder_username,
        "verification_status": row[3],
        "created_at": row[5].isoformat() if row[5] else None,
        "notification_dt": row[7].isoformat() if row[7] else None,
        "region": row[8],
        "province_name": row[9],
        "municipality_name": row[10],
        "barangay_name": row[11],
        "general_category": row[12],
        "sub_category": row[13],
        "alarm_level": row[14],
        "estimated_damage_php": float(row[15]) if row[15] is not None else None,
        "total_response_time_minutes": row[16],
        "casualty_severity": row[17],
        "data_hash": row[6],
        "sync_status": row[18],
        "has_wildland_afor": has_wildland_afor,
    }


@router.get("/incidents/analyst/{incident_id}/wildland")
def get_analyst_incident_wildland_detail(
    incident_id: int,
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
):
    """
    National Analyst wildland AFOR detail for a verified, non-archived incident.

    Requires: NATIONAL_ANALYST or SYSTEM_ADMIN.
    """
    incident_row = db.execute(
        text("""
            SELECT incident_id, reference_number, verification_status, is_archived
            FROM wims.fire_incidents
            WHERE incident_id = :iid
        """),
        {"iid": incident_id},
    ).fetchone()

    if (
        not incident_row
        or incident_row[2] != "VERIFIED"
        or bool(incident_row[3])
    ):
        raise HTTPException(status_code=404, detail="Incident not found")

    wildland_row = db.execute(
        text("""
            SELECT *
            FROM wims.incident_wildland_afor
            WHERE incident_id = :iid
        """),
        {"iid": incident_id},
    ).fetchone()

    if not wildland_row:
        raise HTTPException(status_code=404, detail="Wildland AFOR not found")

    wildland_id = wildland_row._mapping["incident_wildland_afor_id"]
    alarm_rows = db.execute(
        text("""
            SELECT sort_order, alarm_status, time_declared, ground_commander
            FROM wims.wildland_afor_alarm_statuses
            WHERE incident_wildland_afor_id = :wildland_id
            ORDER BY sort_order, wildland_afor_alarm_status_id
        """),
        {"wildland_id": wildland_id},
    ).fetchall()
    assistance_rows = db.execute(
        text("""
            SELECT sort_order, organization_or_unit, detail
            FROM wims.wildland_afor_assistance_rows
            WHERE incident_wildland_afor_id = :wildland_id
            ORDER BY sort_order, wildland_afor_assistance_row_id
        """),
        {"wildland_id": wildland_id},
    ).fetchall()

    return {
        "incident_id": incident_row[0],
        "reference_number": incident_row[1],
        "wildland": _analyst_row_dict(wildland_row),
        "alarm_statuses": [_analyst_row_dict(row) for row in alarm_rows],
        "assistance_rows": [_analyst_row_dict(row) for row in assistance_rows],
    }
