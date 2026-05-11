"""Spatial + temporal duplicate detection for fire incidents.

Usage
-----
    from services.duplicate_detection import check_for_duplicate

    matched_id = check_for_duplicate(
        db,
        incident_id=123,
        region_id=4,
        alarm_level="1st",
        incident_date="2026-05-09",   # or None to skip date filter
        lat=14.5995,
        lon=120.9842,
        general_category="STRUCTURAL",
        exclude_statuses=("DRAFT", "REJECTED", "REPLACED"),
    )
    if matched_id:
        # duplicate found
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def check_for_duplicate(
    db: Session,
    *,
    incident_id: int,
    region_id: int,
    alarm_level: str | None,
    incident_date: str | None,
    lat: float | None,
    lon: float | None,
    general_category: str | None = None,
    incident_type_code: str | None = None,
    exclude_statuses: tuple[str, ...] = (),
    verified_window_seconds: int | None = None,
) -> int | None:
    """Return the incident_id of a duplicate, or None if no duplicate is found.

    Detection logic
    ---------------
    Primary (when lat/lon provided):
        ST_DWithin(location, point, 5000 metres) + same region_id + not archived
        + status NOT IN exclude_statuses.
        When incident_date is provided, also checks ±1 day window on notification_dt.
        When incident_date is None, the date filter is skipped (spatial-only match).

    When ``verified_window_seconds`` is set (bulk-accept consecutive check):
        Only VERIFIED incidents updated within that many seconds of NOW() are
        considered — used to catch back-to-back accepts of the same incident.

    Fallback (when lat/lon is None or primary finds nothing):
        Text match on region_id + (general_category OR incident_type_code).
        Date filter applied only when incident_date is provided.

    Parameters
    ----------
    incident_id:
        The incident being checked — excluded from results.
    region_id:
        Region the incident belongs to.
    alarm_level:
        Alarm level string (unused in query; reserved for future tightening).
    incident_date:
        YYYY-MM-DD date string in Asia/Manila (PHT) representing the fire date,
        or None to skip the date constraint entirely (spatial/category match only).
    lat, lon:
        Coordinates of the incident. Pass None to skip spatial check.
    general_category:
        e.g. "STRUCTURAL", "VEHICULAR", "WILDLAND".
    incident_type_code:
        3–4 letter AFOR type code (e.g. "APT", "INF").
    exclude_statuses:
        Tuple of verification_status values to ignore.
    verified_window_seconds:
        When set, only VERIFIED rows updated within this many seconds are checked.
        Intended for consecutive bulk-accept duplicate guard.
    """
    skip_statuses: list[str] = list(exclude_statuses) if exclude_statuses else []

    # -----------------------------------------------------------------------
    # Primary: spatial match (5 km radius) + optional date window
    # -----------------------------------------------------------------------
    if lat is not None and lon is not None:
        extra_clauses = ""
        params: dict = {
            "lon": float(lon),
            "lat": float(lat),
            "rid": region_id,
            "cur_id": incident_id,
        }

        # Date filter — only when a fire date is known
        if incident_date is not None:
            params["fire_date"] = incident_date
            extra_clauses += """
                  AND  (
                         nd.notification_dt IS NULL
                         OR DATE(nd.notification_dt AT TIME ZONE 'Asia/Manila')
                              BETWEEN DATE(CAST(:fire_date AS date)) - INTERVAL '1 day'
                                  AND DATE(CAST(:fire_date AS date)) + INTERVAL '1 day'
                       )"""

        if skip_statuses:
            params["skip_statuses"] = skip_statuses
            extra_clauses += " AND fi.verification_status != ALL(:skip_statuses)"

        if verified_window_seconds is not None:
            params["window_seconds"] = verified_window_seconds
            extra_clauses += (
                " AND fi.verification_status = 'VERIFIED'"
                " AND fi.updated_at > NOW() - (:window_seconds || ' seconds')::interval"
            )

        row = db.execute(
            text(
                f"""
                SELECT fi.incident_id
                FROM   wims.fire_incidents fi
                LEFT JOIN wims.incident_nonsensitive_details nd
                       ON nd.incident_id = fi.incident_id
                WHERE  fi.region_id  = :rid
                  AND  fi.incident_id != :cur_id
                  AND  fi.is_archived = FALSE
                  AND  ST_DWithin(
                           fi.location::geography,
                           ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                           5000
                       )
                {extra_clauses}
                ORDER BY fi.updated_at DESC
                LIMIT 1
                """
            ),
            params,
        ).fetchone()

        if row:
            return int(row[0])

    # -----------------------------------------------------------------------
    # Fallback: region + category match + optional date window
    # -----------------------------------------------------------------------
    if not general_category and not incident_type_code:
        return None

    cat_conditions: list[str] = []
    fallback_params: dict = {
        "rid": region_id,
        "cur_id": incident_id,
    }

    if incident_type_code:
        cat_conditions.append(
            "(:type_code IS NOT NULL AND fi.incident_type_code = :type_code)"
        )
        fallback_params["type_code"] = incident_type_code
    if general_category:
        cat_conditions.append(
            "(:gen_cat IS NOT NULL AND nd.general_category = :gen_cat)"
        )
        fallback_params["gen_cat"] = general_category

    cat_sql = " OR ".join(cat_conditions)

    date_clause = ""
    if incident_date is not None:
        fallback_params["fire_date"] = incident_date
        date_clause = """
              AND  (
                     nd.notification_dt IS NULL
                     OR DATE(nd.notification_dt AT TIME ZONE 'Asia/Manila')
                          BETWEEN DATE(CAST(:fire_date AS date)) - INTERVAL '1 day'
                              AND DATE(CAST(:fire_date AS date)) + INTERVAL '1 day'
                   )"""

    status_clause = ""
    if skip_statuses:
        fallback_params["skip_statuses"] = skip_statuses
        status_clause = " AND fi.verification_status != ALL(:skip_statuses)"

    if verified_window_seconds is not None:
        fallback_params["window_seconds"] = verified_window_seconds
        status_clause += (
            " AND fi.verification_status = 'VERIFIED'"
            " AND fi.updated_at > NOW() - (:window_seconds || ' seconds')::interval"
        )

    fallback_row = db.execute(
        text(
            f"""
            SELECT fi.incident_id
            FROM   wims.fire_incidents fi
            LEFT JOIN wims.incident_nonsensitive_details nd
                   ON nd.incident_id = fi.incident_id
            WHERE  fi.region_id  = :rid
              AND  fi.incident_id != :cur_id
              AND  fi.is_archived = FALSE
              AND  ({cat_sql})
            {date_clause}
            {status_clause}
            ORDER BY fi.updated_at DESC
            LIMIT 1
            """
        ),
        fallback_params,
    ).fetchone()

    return int(fallback_row[0]) if fallback_row else None
