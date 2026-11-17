"""Regional Office API — AFOR import routes."""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_encoder_or_admin
from auth import get_db_with_rls
from services.afor_import import (
    AforCommitRequest,
    AforCommitResponse,
    AforParseResponse,
    parse_csv_content,
    parse_xlsx_content,
)
from services.afor_import.commit import (
    AforCommitDependencies,
    commit_afor_import_command,
    resolve_import_region,
)
from services.afor_import.models import AforRegionDetectResponse
from services.regional_incidents.helpers import (
    insert_incident_verification_history as _insert_incident_verification_history,
    region_text_matches as _region_text_matches,
)
from services.kms import get_crypto_provider
from utils.audit import trusted_client_ip, log_system_audit
from utils.upload_validation import (
    check_magic_bytes,
    check_xlsx_decompression_bomb,
    safe_read_upload,
    sanitize_filename,
    validate_extension,
)

logger = logging.getLogger("wims.regional")
router = APIRouter()


def _get_security_provider():
    """Return the correct crypto provider based on WIMS_CRYPTO_PROVIDER env var."""
    return get_crypto_provider()


async def _read_validated_upload(file: UploadFile) -> tuple[bytes, str]:
    """Deep upload checks (#391): filename, extension, size cap, magic bytes, bomb defense."""
    safe_name = sanitize_filename(file.filename)
    ext = validate_extension(safe_name, ["xlsx", "csv"])

    # App-level size cap (10 MB for AFOR per issue #391)
    _max_afor_bytes = int(os.getenv("WIMS_MAX_AFOR_BYTES", str(10 * 1024 * 1024)))
    content = await safe_read_upload(file, _max_afor_bytes)

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Magic byte verification ensures claimed extension matches real content.
    check_magic_bytes(content, ext)

    # Decompression bomb defense (XLSX only — CSVs are plain text).
    if ext == "xlsx":
        check_xlsx_decompression_bomb(content)
    return content, ext


def _parse_rows(content: bytes, ext: str, region_id: int):
    try:
        if ext == "csv":
            decoded = content.decode("utf-8-sig")  # Handle BOM
            return parse_csv_content(decoded, region_id)
        return parse_xlsx_content(content, region_id)
    except ValueError as e:
        logger.warning("AFOR type detection failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to parse AFOR file")
        raise HTTPException(status_code=400, detail="Failed to parse file")


def _file_region_text(rows, form_kind: str) -> str:
    if form_kind != "STRUCTURAL_AFOR":
        return ""
    first_valid = next((r for r in rows if r.status == "VALID"), None)
    return ((first_valid.data.get("_region_text") or "") if first_valid else "").strip()


@router.post("/afor/detect-region", response_model=AforRegionDetectResponse)
async def detect_afor_region(
    file: UploadFile = File(...),
    user: dict = Depends(get_encoder_or_admin),
    db: Session = Depends(get_db_with_rls),
):
    """SYSTEM_ADMIN helper: read the region text printed on an AFOR file and suggest a region.

    Used only to pre-select the region dropdown; nothing is persisted. The admin
    always makes the final choice.
    """
    if user.get("role") != "SYSTEM_ADMIN":
        raise HTTPException(status_code=403, detail="SYSTEM_ADMIN privileges required")
    content, ext = await _read_validated_upload(file)
    rows, form_kind = _parse_rows(content, ext, 0)
    region_text = _file_region_text(rows, form_kind)
    suggested: int | None = None
    if region_text:
        for rid, rname in db.execute(
            text("SELECT region_id, region_name FROM wims.ref_regions ORDER BY region_id")
        ).fetchall():
            if _region_text_matches(rname, region_text):
                suggested = rid
                break
    return AforRegionDetectResponse(
        file_region_text=region_text or None, suggested_region_id=suggested
    )


@router.post("/afor/import", response_model=AforParseResponse)
async def import_afor_file(
    file: UploadFile = File(...),
    region_id: int | None = Form(None),
    user: dict = Depends(get_encoder_or_admin),
    db: Session = Depends(get_db_with_rls),
    request: Request = None,
):
    """
    Upload and parse an AFOR file (.xlsx or .csv).
    Returns parsed rows with validation status for preview before commit.

    REGIONAL_ENCODER: bound to their assigned region (``region_id`` is ignored and a
    file/region mismatch is rejected). SYSTEM_ADMIN: ``region_id`` is required; a
    mismatch with the file's region text is reported in the response (warn, allow)
    and recorded in the audit log.
    """
    is_admin = user.get("role") == "SYSTEM_ADMIN"
    region_id = resolve_import_region(db, user, region_id)

    content, ext = await _read_validated_upload(file)
    rows, form_kind = _parse_rows(content, ext, region_id)

    if form_kind == "WILDLAND_AFOR":
        raise HTTPException(
            status_code=400,
            detail=(
                "Wildland-specific AFOR import is deprecated. Use the structural "
                "AFOR import or encode wildland incidents through the standard "
                "incident form category/sub-category fields."
            ),
        )

    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="No data rows found in file")

    # Region check against the region text printed on the file.
    xlsx_region_text = _file_region_text(rows, form_kind)
    region_mismatch = False
    if xlsx_region_text:
        selected_row = db.execute(
            text("SELECT region_name FROM wims.ref_regions WHERE region_id = :rid"),
            {"rid": region_id},
        ).fetchone()
        if selected_row and not _region_text_matches(selected_row[0], xlsx_region_text):
            if is_admin:
                # Admin: warn in the response, allow, and audit (see below).
                region_mismatch = True
            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Region mismatch: this AFOR is for '{xlsx_region_text}', "
                        f"but you are assigned to '{selected_row[0]}'. "
                        "You can only import AFORs within your assigned region."
                    ),
                )

    valid_count = sum(1 for r in rows if r.status == "VALID")

    # Audit log entry (D20 / issue #394) — preview / parse phase. The actual
    # mutations happen in commit_afor_import, which writes its own audit row.
    # sensitive=False: parse does not mutate any data, so audit gaps are
    # acceptable forensic noise.
    try:
        log_system_audit(
            db=db,
            user_id=user["user_id"],
            action_type="AFOR_IMPORT_PARSE",
            table_affected="wims.afor_imports",
            record_id=None,
            request=request,
            new_values={
                "file_name": file.filename,
                "form_kind": form_kind,
                "total_rows": len(rows),
                "valid_rows": valid_count,
                **(
                    {
                        "actor_role": "SYSTEM_ADMIN",
                        "chosen_region_id": region_id,
                        "file_region_text": xlsx_region_text or None,
                        "region_mismatch": region_mismatch,
                    }
                    if is_admin
                    else {}
                ),
            },
        )
        db.commit()
    except Exception:
        # Audit failures are non-fatal.
        logger.exception("Failed to write AFOR import audit log")

    return AforParseResponse(
        total_rows=len(rows),
        valid_rows=valid_count,
        invalid_rows=len(rows) - valid_count,
        rows=rows,
        form_kind=form_kind,
        region_id=region_id,
        file_region_text=xlsx_region_text or None,
        region_mismatch=region_mismatch,
    )


@router.post("/afor/commit")
async def commit_afor_import(
    request: Request,
    user: Annotated[dict, Depends(get_encoder_or_admin)],
    db: Annotated[Session, Depends(get_db_with_rls)],
):
    """Commit validated AFOR rows through the AFOR import command module."""
    try:
        raw_body: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None

    body = AforCommitRequest.model_validate(raw_body)
    if body.form_kind == "WILDLAND_AFOR":
        raise HTTPException(
            status_code=400,
            detail=(
                "Wildland-specific AFOR commit is deprecated. Use the structural "
                "AFOR import or encode wildland incidents through the standard "
                "incident form category/sub-category fields."
            ),
        )
    _request_ip = trusted_client_ip(request)

    def _ivh_with_ip(db, **kwargs):  # type: ignore[no-untyped-def]
        return _insert_incident_verification_history(db, request_ip=_request_ip, **kwargs)

    result = commit_afor_import_command(
        db,
        user,
        body,
        raw_body,
        AforCommitDependencies(
            insert_incident_verification_history=_ivh_with_ip,
            get_security_provider=_get_security_provider,
        ),
    )

    # Audit log entry (D20 / issue #394) — commit phase. The actual
    # mutations are performed by commit_afor_import_command above; we
    # write the audit row after it returns. sensitive=False: this is a
    # batch write, the commit has already succeeded, and the audit gap
    # is acceptable forensic noise (matches the upload_bundle pattern).
    if result.get("status") != "DUPLICATE_CHECK_REQUIRED":
        inserted = (
            result.get("inserted") or result.get("incident_ids") or result.get("imported") or []
        )
        log_system_audit(
            db=db,
            user_id=user["user_id"],
            action_type="AFOR_IMPORT_COMMIT",
            table_affected="wims.afor_imports",
            record_id=None,
            request=request,
            new_values={
                "form_kind": body.form_kind,
                "region_id": (
                    body.region_id
                    if user.get("role") == "SYSTEM_ADMIN"
                    else user["assigned_region_id"]
                ),
                **(
                    {
                        "actor_role": "SYSTEM_ADMIN",
                        "chosen_region_id": body.region_id,
                        "file_region_text": next(
                            (
                                str(r.get("_region_text")).strip()
                                for r in body.rows
                                if r.get("_region_text")
                            ),
                            None,
                        ),
                    }
                    if user.get("role") == "SYSTEM_ADMIN"
                    else {}
                ),
                "row_count": len(body.rows) if hasattr(body, "rows") else None,
                "inserted_count": len(inserted) if isinstance(inserted, list) else 0,
                "batch_id": result.get("batch_id"),
            },
        )
        db.commit()

    if result.get("status") == "DUPLICATE_CHECK_REQUIRED":
        return result
    return AforCommitResponse.model_validate(result)
