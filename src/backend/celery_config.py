"""Celery app configuration â€” shared by main and tasks to avoid circular imports."""

import os

from celery import Celery
from celery.schedules import crontab


SCHEDULE_CHECK_INTERVAL = int(os.environ.get("SCHEDULE_CHECK_INTERVAL", 300))

KMS_ROTATION_ENABLED = (
    os.environ.get("WIMS_KMS_ROTATION_ENABLED", "true").strip().lower() != "false"
)

MV_REFRESH_INTERVAL = int(os.environ.get("CELERY_MV_REFRESH_INTERVAL", 3600 * 6))
SCHEDULE_CHECK_INTERVAL = int(os.environ.get("SCHEDULE_CHECK_INTERVAL", 300))

celery_app = Celery(
    "wims_worker",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get(
        "CELERY_RESULT_BACKEND", os.environ.get("REDIS_URL", "redis://redis:6379/0")
    ),
    include=[
        "tasks.analytics_refresh",
        "tasks.drafts",
        "tasks.exports",
        "tasks.monitoring",
        "tasks.notifications",
        "tasks.password_expiry",
        "tasks.scheduled_backup",
    ],
)

# The tasks package contains modules rather than app-style tasks.py files, so
# list them explicitly to ensure workers register every scheduled task.
celery_app.conf.imports = (
    "tasks.analytics_refresh",
    "tasks.anomaly_detection",
    "tasks.drafts",
    "tasks.exports",
    "tasks.kms_rotation",
    "tasks.monitoring",
    "tasks.notifications",
    "tasks.password_expiry",
    "tasks.scheduled_backup",
    "tasks.scheduled_reports",
)
# Auto-discover task modules instead of side-effect imports in main.py
celery_app.autodiscover_tasks(["tasks"])
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=(
        "tasks.analytics_refresh",
        "tasks.anomaly_detection",
        "tasks.drafts",
        "tasks.exports",
        "tasks.kms_rotation",
        "tasks.monitoring",
        "tasks.notifications",
        "tasks.password_expiry",
        "tasks.scheduled_backup",
        "tasks.scheduled_reports",
    ),
    # Refresh interval in seconds. Default: 6 hours.
    # Override via CELERY_MV_REFRESH_INTERVAL env var.
    CELERY_MV_REFRESH_INTERVAL=MV_REFRESH_INTERVAL,
    beat_schedule={
        # Refresh analytics materialized views every N seconds (default 6 hours).
        # CONCURRENTLY keeps reads unblocked during refresh.
        "refresh-analytics-mvs": {
            "task": "analytics.refresh_materialized_views",
            "schedule": MV_REFRESH_INTERVAL,
        },
        # M4-E: Auto-archive DRAFT incidents older than 30 days. Runs daily at 02:00 UTC.
        "expire-stale-drafts-daily": {
            "task": "tasks.drafts.expire_old_drafts",
            "schedule": crontab(hour=2, minute=0),
        },
        # M6-H: Worker heartbeat â€” every 30 seconds
        "worker-heartbeat": {
            "task": "tasks.monitoring.worker_heartbeat",
            "schedule": 30.0,
        },
        "snapshot-system-metrics": {
            "task": "tasks.monitoring.snapshot_system_metrics",
            "schedule": 60.0,
        },
        # M13b: Weekly analytics report â€” Monday 07:00 UTC
        "send-weekly-report-email": {
            "task": "tasks.notifications.send_weekly_report_email",
            "schedule": crontab(day_of_week=1, hour=7, minute=0),
        },
        # GH #152 Phase 6: Daily KMS key rotation check (03:30 UTC). Needs OpenBao; client
        # installs run without it and set WIMS_KMS_ROTATION_ENABLED=false.
        **(
            {
                "ensure-pii-key-rotation-daily": {
                    "task": "tasks.kms_rotation.ensure_pii_key_rotation",
                    "schedule": crontab(hour=3, minute=30),
                }
            }
            if KMS_ROTATION_ENABLED
            else {}
        ),
        # Turnover Phase 2: 90-day password expiry for SYSTEM_ADMIN / NATIONAL_VALIDATOR
        # (adds UPDATE_PASSWORD in Keycloak; daily 03:45 UTC)
        "enforce-password-expiry-daily": {
            "task": "tasks.password_expiry.enforce_password_expiry",
            "schedule": crontab(hour=3, minute=45),
        },
        # M8: Behavioral anomaly detection — every 60s
        "detect-behavioral-anomalies": {
            "task": "tasks.anomaly_detection.detect_behavioral_anomalies",
            "schedule": 60.0,
        },
        # Issue #88: Check due scheduled reports periodically (default 300s)
        "execute-scheduled-backup": {
            "task": "tasks.scheduled_backup.execute_due_backup",
            "schedule": 300.0,  # every 5 minutes
        },
        "execute-scheduled-reports": {
            "task": "tasks.scheduled_reports.execute_due_reports",
            "schedule": SCHEDULE_CHECK_INTERVAL,
        },
        # Turnover Phase 3: Suricata ingest/rules, AI queue, civilian report/photo/community and
        # IP/device blocklist resync jobs are intentionally unscheduled (source kept).
    },
)
