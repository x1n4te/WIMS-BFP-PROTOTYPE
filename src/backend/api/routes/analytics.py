"""National Analyst Analytics API — Read-only Intelligence Loop.

All endpoints require NATIONAL_ANALYST or SYSTEM_ADMIN.
Scoped to verified, non-archived incidents only.
Queries wims.analytics_incident_facts (read model) instead of raw operational tables.
"""

from __future__ import annotations

import os
from typing import Annotated, Any, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from celery_config import celery_app
from auth import get_analyst_or_admin
from database import get_db_with_rls
from services.analytics_read_model import (
    count_in_range,
    get_filter_options,
    get_heatmap_points,
    get_trends,
    get_type_distribution,
    get_response_time_by_region,
    get_compare_regions,
    get_top_n,
    verify_indexed_access,
)

from tasks.exports import (
    export_incidents_csv_task,
    export_incidents_pdf_task,
    export_incidents_excel_task,
)
from tasks.analytics_refresh import refresh_materialized_views

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.post("/refresh-views", status_code=status.HTTP_202_ACCEPTED)
def trigger_materialized_view_refresh(
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
):
    """Queue a non-blocking CONCURRENTLY refresh for analytics materialized views."""
    result = refresh_materialized_views.delay(concurrent=True)
    return {"task_id": result.id, "status": "queued"}


@router.get("/heatmap")
def get_heatmap(
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    region_id: Optional[int] = Query(None),
    region_ids: Optional[str] = Query(None, description="Comma-separated region IDs"),
    province: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    alarm_level: Optional[str] = None,
    incident_type: Optional[str] = None,
    casualty_severity: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    damage_min: Optional[float] = Query(None, ge=0),
    damage_max: Optional[float] = Query(None, ge=0),
):
    """
    GeoJSON-compatible heatmap data for verified incidents.
    Uses wims.analytics_incident_facts (indexed access).
    """
    if damage_min is not None and damage_max is not None and damage_max < damage_min:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail="damage_max must be greater than or equal to damage_min",
        )

    parsed_region_ids: Optional[list[int]] = None
    if region_ids:
        try:
            parsed_region_ids = [int(x.strip()) for x in region_ids.split(",") if x.strip()]
        except ValueError:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=422, detail="region_ids must be comma-separated integers"
            )

    points = get_heatmap_points(
        db,
        start_date=start_date,
        end_date=end_date,
        region_id=region_id,
        region_ids=parsed_region_ids,
        province=province,
        municipality=municipality,
        alarm_level=alarm_level,
        incident_type=incident_type,
        casualty_severity=casualty_severity,
        damage_min=damage_min,
        damage_max=damage_max,
    )
    return data


@router.post("/incidents/{incident_id}/narrative")
async def generate_narrative(
    incident_id: int,
    user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
):
    """
    Generate an AI narrative for a verified fire incident via Qwen2.5-3B.
    Only works on VERIFIED incidents. Stores result in fire_incidents.ai_narrative.
    """
    from services.ai_service import generate_incident_narrative

    return await generate_incident_narrative(incident_id, db)


@router.post("/incidents/batch-narratives", status_code=202)
def trigger_batch_narratives(
    user: Annotated[dict, Depends(get_analyst_or_admin)],
    limit: int = Query(default=50, ge=1, le=500),
):
    """
    Trigger batch AI narrative generation for VERIFIED incidents
    without narratives. Dispatches to Celery task.
    """
    from tasks.narrative import batch_generate_narratives

    task = batch_generate_narratives.delay(limit=limit)
    return {"task_id": task.id, "limit": limit}


@router.get("/response-time-by-region")
def get_response_time_by_region_route(
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    region_id: Optional[int] = Query(None),
    province: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    incident_type: Optional[str] = None,
    alarm_level: Optional[str] = None,
    casualty_severity: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    damage_min: Optional[float] = Query(None, ge=0),
    damage_max: Optional[float] = Query(None, ge=0),
):
    """Average/min/max response time grouped by region."""
    data = get_response_time_by_region(
        db,
        start_date=start_date,
        end_date=end_date,
        region_id=region_id,
        province=province,
        municipality=municipality,
        incident_type=incident_type,
        alarm_level=alarm_level,
        casualty_severity=casualty_severity,
        damage_min=damage_min,
        damage_max=damage_max,
    )
    return data


@router.get("/compare-regions")
def compare_regions_route(
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
    region_ids: str = Query(..., description="Comma-separated region IDs (min 2)"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    province: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    incident_type: Optional[str] = None,
    alarm_level: Optional[str] = None,
    casualty_severity: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    damage_min: Optional[float] = Query(None, ge=0),
    damage_max: Optional[float] = Query(None, ge=0),
):
    """Cross-region comparison. Requires at least 2 region IDs."""
    from fastapi import HTTPException

    try:
        parsed = [int(x.strip()) for x in region_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=422, detail="region_ids must be comma-separated integers")
    if len(parsed) < 2:
        raise HTTPException(status_code=422, detail="At least 2 region_ids required for comparison")
    data = get_compare_regions(
        db,
        region_ids=parsed,
        start_date=start_date,
        end_date=end_date,
        province=province,
        municipality=municipality,
        incident_type=incident_type,
        alarm_level=alarm_level,
        casualty_severity=casualty_severity,
        damage_min=damage_min,
        damage_max=damage_max,
    )
    return data


@router.get("/top-n")
def top_n_route(
    _user: Annotated[dict, Depends(get_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
    metric: str = Query(..., pattern="^(incidents|response_time|casualties)$"),
    dimension: str = Query(..., pattern="^(fire_station|region|municipality)$"),
    limit: int = Query(10, ge=1, le=50),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    region_id: Optional[int] = Query(None),
    province: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    incident_type: Optional[str] = None,
    alarm_level: Optional[str] = None,
    casualty_severity: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    damage_min: Optional[float] = Query(None, ge=0),
    damage_max: Optional[float] = Query(None, ge=0),
):
    """Configurable top-N analysis by metric and dimension."""
    data = get_top_n(
        db,
        metric=metric,
        dimension=dimension,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        region_id=region_id,
        province=province,
        municipality=municipality,
        incident_type=incident_type,
        alarm_level=alarm_level,
        casualty_severity=casualty_severity,
        damage_min=damage_min,
        damage_max=damage_max,
    )
    return data
