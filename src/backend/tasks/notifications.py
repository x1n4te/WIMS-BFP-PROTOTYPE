"""Celery tasks — email notifications (FCM push removed in turnover Phase 3)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone

import aiosmtplib
from sqlalchemy import text

from celery_config import celery_app
from database import get_session, SYSTEM_TASK_USER_ID
from services.email.sender import send_email as _send_email

logger = logging.getLogger(__name__)

# =============================================================================
# Email tasks (M13b) — security_alert wired in admin/security.py,
# weekly_report wired below, account_locked deferred (#138).
# =============================================================================


@celery_app.task(
    bind=True,
    name="tasks.notifications.send_email",
    autoretry_for=(aiosmtplib.SMTPException, ConnectionError, TimeoutError, OSError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=5,
)
def send_email_task(
    self,
    to: str | list[str],
    template_name: str,
    context: dict,
) -> dict:
    """Render and send a templated email asynchronously.

    Args:
        to: Recipient email address (or list of addresses).
        template_name: Name of a Jinja2 HTML template in services/email/templates/
                      (without the .html.j2 extension).
        context: Jinja2 template variable dictionary.

    Raises:
        Retries with exponential backoff on transient SMTP/network exceptions
        (max 5 retries, up to 10 minutes between attempts).
        Permanent failures (template/context/type errors) fail fast.
        Does NOT query RLS tables.
    """
    try:
        _send_email(to, template_name, context)
        logger.info("Email sent via send_email_task: to=%s template=%s", to, template_name)
        return {"ok": True, "to": to, "template": template_name}
    except Exception as exc:
        remaining = self.max_retries - self.request.retries
        logger.warning(
            "send_email_task failed for to=%s template=%s: %s — retry %d/%d",
            to,
            template_name,
            exc,
            remaining,
            self.max_retries,
        )
        raise


@celery_app.task(
    name="tasks.notifications.send_weekly_report_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=3600,
    max_retries=3,
)
def send_weekly_report_email() -> dict:
    """
    Send weekly analytics summary email to all active SYSTEM_ADMIN users.
    Runs every Monday at 07:00 UTC via Celery beat.
    Queries analytics_incident_facts for 7-day totals and top region.
    """
    db = get_session(SYSTEM_TASK_USER_ID)
    try:
        # Compute 7-day range
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=7)
        week_range = f"{start_date.isoformat()} – {end_date.isoformat()}"

        # Query 7-day incident count from analytics_incident_facts
        total_incidents = (
            db.execute(
                text(
                    """
                    SELECT COUNT(*) FROM wims.analytics_incident_facts
                    WHERE notification_date >= :start_date AND notification_date <= :end_date
                    """
                ),
                {"start_date": start_date, "end_date": end_date},
            ).scalar()
            or 0
        )

        # Query top region by incident count
        top_region_row = db.execute(
            text(
                """
                SELECT r.region_code, COUNT(*) AS cnt
                FROM wims.analytics_incident_facts a
                JOIN wims.ref_regions r ON r.region_id = a.region_id
                WHERE a.notification_date >= :start_date AND a.notification_date <= :end_date
                GROUP BY r.region_code
                ORDER BY cnt DESC
                LIMIT 1
                """
            ),
            {"start_date": start_date, "end_date": end_date},
        ).fetchone()
        top_region = top_region_row[0] if top_region_row else "N/A"

        # Fetch SYSTEM_ADMIN emails who have opted into email notifications
        # (security_alert in admin/security.py intentionally bypasses opt-in — critical alerts)
        admin_emails = [
            row[0]
            for row in db.execute(
                text(
                    "SELECT email FROM wims.users"
                    " WHERE role = 'SYSTEM_ADMIN' AND is_active = TRUE"
                    " AND email IS NOT NULL AND email_opt_in = TRUE"
                )
            ).fetchall()
        ]

        if not admin_emails:
            logger.info("Weekly report: no SYSTEM_ADMIN emails configured, skipping")
            return {"sent": 0, "reason": "no_recipients"}

        frontend_url = os.environ.get("NEXT_PUBLIC_APP_URL", "http://localhost:3000")
        report_link = f"{frontend_url}/admin/analytics"

        send_email_task.delay(
            to=admin_emails,
            template_name="weekly_report",
            context={
                "week_range": week_range,
                "total_incidents": total_incidents,
                "top_region": top_region,
                "report_link": report_link,
            },
        )
        logger.info(
            "Weekly report dispatched to %d admin(s): %d incidents, top region: %s",
            len(admin_emails),
            total_incidents,
            top_region,
        )
        return {
            "sent": len(admin_emails),
            "total_incidents": total_incidents,
            "top_region": top_region,
        }

    except Exception:
        db.rollback()
        logger.exception("Weekly report task failed")
        raise
    finally:
        db.close()
