"""Celery tasks for analytics exports."""

from __future__ import annotations

import csv
import json
import logging
import os
import uuid
from typing import Any, Callable

from sqlalchemy import text

from celery_config import celery_app
from database import get_session, set_rls_context
from services.analytics_read_model import get_export_rows

logger = logging.getLogger(__name__)

ALLOWED_EXPORT_COLUMNS = {
    "incident_id",
    "notification_dt",
    "alarm_level",
    "general_category",
    "sub_category",
    "fire_origin",
    "extent_of_damage",
    "structures_affected",
    "households_affected",
    "individuals_affected",
    "vehicles_affected",
    "total_response_time_minutes",
    "total_gas_consumed_liters",
    "extent_total_floor_area_sqm",
    "extent_total_land_area_hectares",
    "civilian_injured",
    "civilian_deaths",
    "firefighter_injured",
    "firefighter_deaths",
    "fire_station_name",
    "region_id",
    "verification_status",
    "estimated_damage_php",
    "barangay_name",
    "municipality_name",
    "province_name",
}

DEFAULT_EXPORT_COLUMNS = [
    "incident_id",
    "notification_dt",
    "region_id",
    "province_name",
    "municipality_name",
    "barangay_name",
    "alarm_level",
    "general_category",
    "sub_category",
    "estimated_damage_php",
    "total_response_time_minutes",
]

EXPORT_DIR = os.environ.get("EXPORT_DIR", "/tmp/wims-exports")


def _serialize_value(v: Any) -> str:
    if v is None:
        return ""
    if hasattr(v, "isoformat"):
        return str(v.isoformat())
    return str(v)


def _valid_columns(columns: list[str]) -> list[str]:
    valid_cols = [c for c in columns if c in ALLOWED_EXPORT_COLUMNS]
    return valid_cols or DEFAULT_EXPORT_COLUMNS


def _write_csv(path: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: _serialize_value(row.get(col)) for col in columns})


def _write_xlsx(path: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Incidents"
    worksheet.append(columns)
    for row in rows:
        worksheet.append([_serialize_value(row.get(col)) for col in columns])
    workbook.save(path)


def _write_pdf(path: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=landscape(letter), title="WIMS-BFP AFOR Export")
    story = [
        Paragraph("WIMS-BFP AFOR Incident Export", styles["Title"]),
        Paragraph(f"Rows: {len(rows)}", styles["Normal"]),
        Spacer(1, 12),
    ]
    table_data = [columns]
    table_data.extend([[_serialize_value(row.get(col)) for col in columns] for row in rows])
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7f1d1d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    doc.build(story)


def _insert_export_log(
    db: Any,
    *,
    user_id: str,
    export_format: str,
    filters: dict[str, Any],
    columns: list[str],
    task_id: str | None,
    path: str,
    content_type: str,
    row_count: int,
) -> None:
    db.execute(
        text("""
            INSERT INTO wims.analytics_export_log
                (user_id, format, filters_json, columns_json, row_count,
                 task_id, file_path, file_name, content_type)
            VALUES
                (:user_id, :format, CAST(:filters_json AS jsonb), CAST(:columns_json AS jsonb),
                 :row_count, :task_id, :file_path, :file_name, :content_type)
        """),
        {
            "user_id": user_id,
            "format": export_format,
            "filters_json": json.dumps(filters or {}),
            "columns_json": json.dumps(columns),
            "row_count": row_count,
            "task_id": task_id,
            "file_path": path,
            "file_name": os.path.basename(path),
            "content_type": content_type,
        },
    )
    db.commit()


def _export(
    *,
    task_id: str | None,
    user_id: str,
    filters: dict[str, Any],
    columns: list[str],
    export_format: str,
    extension: str,
    content_type: str,
    writer: Callable[[str, list[dict[str, Any]], list[str]], None],
) -> str:
    valid_cols = _valid_columns(columns)
    logger.info(
        "%s export started: user_id=%s, filters=%s, columns=%s",
        export_format.upper(),
        user_id,
        filters,
        valid_cols,
    )

    db = get_session()
    try:
        set_rls_context(db, uuid.UUID(user_id))
        rows = get_export_rows(db, filters or {}, valid_cols)
        os.makedirs(EXPORT_DIR, exist_ok=True)
        path = os.path.join(EXPORT_DIR, f"analytics_export_{uuid.uuid4().hex[:12]}.{extension}")
        writer(path, rows, valid_cols)
        _insert_export_log(
            db,
            user_id=user_id,
            export_format=export_format,
            filters=filters or {},
            columns=valid_cols,
            task_id=task_id,
            path=path,
            content_type=content_type,
            row_count=len(rows),
        )
    finally:
        db.close()

    logger.info("%s export complete: %d rows -> %s", export_format.upper(), len(rows), path)
    return path


@celery_app.task(bind=True, name="tasks.exports.export_incidents_csv")
def export_incidents_csv_task(self, user_id: str, filters: dict[str, Any], columns: list[str]) -> str:
    """Export verified, non-archived incidents to a real CSV file."""
    return _export(
        task_id=getattr(self.request, "id", None),
        user_id=user_id,
        filters=filters,
        columns=columns,
        export_format="csv",
        extension="csv",
        content_type="text/csv",
        writer=_write_csv,
    )


@celery_app.task(bind=True, name="tasks.exports.export_incidents_pdf")
def export_incidents_pdf_task(self, user_id: str, filters: dict[str, Any], columns: list[str]) -> str:
    """Export verified, non-archived incidents to a real PDF file."""
    return _export(
        task_id=getattr(self.request, "id", None),
        user_id=user_id,
        filters=filters,
        columns=columns,
        export_format="pdf",
        extension="pdf",
        content_type="application/pdf",
        writer=_write_pdf,
    )


@celery_app.task(bind=True, name="tasks.exports.export_incidents_excel")
def export_incidents_excel_task(self, user_id: str, filters: dict[str, Any], columns: list[str]) -> str:
    """Export verified, non-archived incidents to a real XLSX file."""
    return _export(
        task_id=getattr(self.request, "id", None),
        user_id=user_id,
        filters=filters,
        columns=columns,
        export_format="excel",
        extension="xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        writer=_write_xlsx,
    )
