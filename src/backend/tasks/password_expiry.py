"""Celery task — 90-day password expiry for privileged roles.

Keycloak's realm-wide ``forceExpiredPasswordChange`` cannot be scoped per role, so
this daily task enforces the rule only where required: for SYSTEM_ADMIN and
NATIONAL_VALIDATOR users whose newest ``password`` credential is older than
PASSWORD_MAX_AGE_DAYS (default 90), it adds the UPDATE_PASSWORD required action,
so the next login forces a change. Every flagged user is audit-logged.

Encoders, analysts and civilians are never touched. Idempotent: a user who already
has UPDATE_PASSWORD pending is skipped (no repeat action, no repeat audit row).
Never logs or stores passwords or credential secrets, only the credential date.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from celery_config import celery_app
from database import _AdminSessionLocal, SYSTEM_TASK_USER_ID, set_rls_context
from services.keycloak_admin import add_required_action, list_role_members_with_password_age
from utils.audit import log_system_audit

logger = logging.getLogger("wims.password_expiry")

PASSWORD_MAX_AGE_DAYS = int(os.environ.get("PASSWORD_MAX_AGE_DAYS", "90"))
EXPIRY_ROLES = ("SYSTEM_ADMIN", "NATIONAL_VALIDATOR")
REQUIRED_ACTION = "UPDATE_PASSWORD"


def password_age_days(created_ms: int | None, now: datetime | None = None) -> float | None:
    """Age in days of a Keycloak credential ``createdDate`` (epoch ms); None if unknown."""
    if created_ms is None:
        return None
    now = now or datetime.now(timezone.utc)
    return (now.timestamp() * 1000 - created_ms) / 86_400_000


def is_password_expired(
    created_ms: int | None, max_age_days: int = PASSWORD_MAX_AGE_DAYS, now: datetime | None = None
) -> bool:
    age = password_age_days(created_ms, now)
    return age is not None and age > max_age_days


@celery_app.task(name="tasks.password_expiry.enforce_password_expiry")
def enforce_password_expiry() -> dict:
    """Flag SYSTEM_ADMIN / NATIONAL_VALIDATOR users whose password is older than the limit."""
    now = datetime.now(timezone.utc)
    summary: dict = {"checked": 0, "flagged": [], "already_flagged": 0, "errors": 0}

    db = _AdminSessionLocal()
    try:
        set_rls_context(db, SYSTEM_TASK_USER_ID)
        for role in EXPIRY_ROLES:
            try:
                members = list_role_members_with_password_age(role)
            except Exception:
                logger.exception("Could not list Keycloak members of role %s", role)
                summary["errors"] += 1
                continue

            for m in members:
                if not m.get("enabled", True):
                    continue
                summary["checked"] += 1
                created_ms = m.get("password_created_ms")
                if not is_password_expired(created_ms, PASSWORD_MAX_AGE_DAYS, now):
                    continue
                if REQUIRED_ACTION in m.get("required_actions", []):
                    summary["already_flagged"] += 1
                    continue
                try:
                    added = add_required_action(m["id"], REQUIRED_ACTION)
                except Exception:
                    logger.exception("Could not flag user %s for password expiry", m.get("username"))
                    summary["errors"] += 1
                    continue
                if not added:
                    summary["already_flagged"] += 1
                    continue

                age = password_age_days(created_ms, now)
                log_system_audit(
                    db=db,
                    user_id=None,
                    action_type="PASSWORD_EXPIRY_FLAGGED",
                    table_affected="users",
                    record_id=None,
                    request=None,
                    new_values={
                        "username": m.get("username"),
                        "role": role,
                        "keycloak_id": m["id"],
                        "password_created_at": datetime.fromtimestamp(
                            created_ms / 1000, tz=timezone.utc
                        ).isoformat(),
                        "password_age_days": round(age, 1) if age is not None else None,
                        "max_age_days": PASSWORD_MAX_AGE_DAYS,
                        "required_action_added": REQUIRED_ACTION,
                    },
                )
                db.commit()
                summary["flagged"].append(m.get("username"))
                logger.info(
                    "Password expiry: flagged %s (%s), age %.0f days", m.get("username"), role, age
                )
        return summary
    finally:
        db.close()
