"""Client-turnover Phase 3: backend trim (civilian/public, Suricata/AI/HITL removed).

Covers:
  * every removed route returns 404 (and kept routes are still mounted)
  * manual breach creation (module 10 no longer depends on the HITL confirm-threat flow)
  * anomaly detection no longer writes security_threat_logs or pushes to the AI queue
  * beat schedule / task registration lists nothing removed
  * system health payload has no Suricata/Ollama component
  * hidden AI config keys, no Turnstile startup hook, compose has no removed services
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import auth
from database import get_db
from main import app

ADMIN = {
    "user_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "keycloak_id": "kid-admin",
    "username": "admin",
    "role": "SYSTEM_ADMIN",
}
ENCODER = {**ADMIN, "user_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", "role": "REGIONAL_ENCODER"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset():
    yield
    app.dependency_overrides.clear()


def _as(user, db=None):
    app.dependency_overrides[auth.get_current_wims_user] = lambda: dict(user)
    app.dependency_overrides[get_db] = lambda: db or MagicMock()
    app.dependency_overrides[auth.get_db_with_rls] = lambda: db or MagicMock()


# ---------------------------------------------------------------------------
# Removed routes -> 404; kept routes still mounted
# ---------------------------------------------------------------------------

REMOVED = [
    ("GET", "/api/civilian/reports"),
    ("POST", "/api/civilian/reports"),
    ("POST", "/api/v1/public/report"),
    ("GET", "/api/public/clusters"),
    ("GET", "/api/public/emergency-services"),
    ("GET", "/api/community/hub"),
    ("GET", "/api/information/announcements"),
    ("GET", "/api/information/emergencies"),
    ("GET", "/api/triage/pending"),
    ("GET", "/api/operations"),
    ("GET", "/api/validator/operational-map"),
    ("GET", "/api/validator/fire-stations"),
    ("GET", "/api/regional/incidents/1/perimeter"),
    ("GET", "/api/regional/perimeters"),
    ("GET", "/api/admin/civilians"),
    ("GET", "/api/admin/community/content"),
    ("GET", "/api/admin/information/announcements"),
    ("GET", "/api/admin/device-blocklist"),
    ("GET", "/api/admin/ip-blocklist"),
    ("GET", "/api/admin/security-logs"),
    ("GET", "/api/admin/security-logs/summary"),
    ("GET", "/api/admin/security-logs/rollups"),
    ("POST", "/api/admin/security-logs/1/analyze"),
    ("PATCH", "/api/admin/security-logs/1"),
    ("POST", "/api/admin/security-logs/1/block"),
    ("POST", "/api/admin/security-logs/1/block-source-ip"),
    ("POST", "/api/admin/security-logs/1/create-incident"),
    ("POST", "/api/admin/security-logs/bulk-action"),
    ("POST", "/api/admin/audit-logs/analyze"),
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/verify-registration"),
    ("POST", "/api/auth/consent"),
    ("GET", "/api/ref/fire-stations"),
    ("GET", "/api/ref/emergency-services"),
]

KEPT = [
    ("GET", "/api/ref/regions"),
    ("GET", "/api/ref/provinces"),
    ("GET", "/api/ref/cities"),
    ("GET", "/api/geocode/search"),
    ("GET", "/api/admin/breach"),
    ("GET", "/api/admin/anomalies"),
    ("GET", "/api/admin/health"),
    ("GET", "/api/dashboard/widgets"),
    ("GET", "/api/analytics/trends"),
    ("POST", "/api/regional/afor/import"),
    ("POST", "/api/auth/keycloak-event"),
]


class TestRoutes:
    @pytest.mark.parametrize("method,path", REMOVED)
    def test_removed_route_is_404(self, client, method, path):
        _as(ADMIN)
        r = client.request(method, path, json={} if method != "GET" else None)
        assert r.status_code in (404, 405), (method, path, r.status_code)
        # 405 only allowed when the path exists for another method; none of these should.
        assert r.status_code == 404, (method, path, r.status_code)

    @pytest.mark.parametrize("method,path", KEPT)
    def test_kept_route_still_mounted(self, client, method, path):
        _as(ADMIN)
        r = client.request(method, path)
        assert r.status_code != 404, (method, path)

    def test_auth_router_keeps_change_and_verify_email(self, client):
        _as(ADMIN)
        assert client.post("/api/auth/change-email", json={}).status_code != 404
        assert client.post("/api/auth/verify-email", json={}).status_code != 404


# ---------------------------------------------------------------------------
# Manual breach (module 10)
# ---------------------------------------------------------------------------


def _breach_row(breach_id=7, log_id=99, detected=None, deadline=None, status="DETECTED"):
    detected = detected or datetime.now(timezone.utc)
    deadline = deadline or detected + timedelta(hours=72)
    return (
        breach_id,
        log_id,
        detected,
        deadline,
        status,
        "Portal",
        "Contact data",
        "n",
        ADMIN["user_id"],
        None,
        detected,
        detected,
    )


class TestManualBreach:
    def _db(self, row=None, emails=(("ops@bfp.test",),)):
        db = MagicMock()
        scalar = MagicMock()
        scalar.scalar.return_value = 99
        insert_breach = MagicMock()
        insert_breach.fetchone.return_value = row or _breach_row()
        email_q = MagicMock()
        email_q.fetchall.return_value = list(emails)
        db.execute.side_effect = [scalar, insert_breach, email_q]
        return db

    def test_admin_creates_breach_without_hitl(self, client):
        db = self._db()
        _as(ADMIN, db)
        with (
            patch("api.routes.admin.breach.log_system_audit") as audit,
            patch("tasks.notifications.send_email_task") as mail,
        ):
            r = client.post(
                "/api/admin/breach",
                json={
                    "summary": "Laptop with exported AFOR data lost",
                    "severity": "HIGH",
                    "affected_systems": "Portal",
                    "data_scope": "Contact data",
                },
            )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["breach_id"] == 7 and body["status"] == "DETECTED"
        # backing threat-log row (NOT NULL FK) then the breach row, in one transaction
        sql = [str(c.args[0]) for c in db.execute.call_args_list]
        assert (
            "INSERT INTO wims.security_threat_logs" in sql[0] and "MANUAL_BREACH_REPORT" in sql[0]
        )
        assert "INSERT INTO wims.breach_notifications" in sql[1]
        assert db.execute.call_args_list[1].args[1]["log_id"] == 99
        db.commit.assert_called_once()
        a = audit.call_args.kwargs
        assert a["action_type"] == "BREACH_DETECTED" and a["new_values"]["source"] == "manual"
        assert a["sensitive"] is True
        mail.delay.assert_called_once()
        assert mail.delay.call_args.kwargs["template_name"] == "breach_alert"
        assert mail.delay.call_args.kwargs["to"] == ["ops@bfp.test"]

    def test_deadline_is_72h_from_detected_at(self, client):
        db = self._db()
        _as(ADMIN, db)
        detected = datetime.now(timezone.utc) - timedelta(hours=5)
        with (
            patch("api.routes.admin.breach.log_system_audit"),
            patch("tasks.notifications.send_email_task"),
        ):
            r = client.post(
                "/api/admin/breach",
                json={"summary": "Misdirected email", "detected_at": detected.isoformat()},
            )
        assert r.status_code == 201
        params = db.execute.call_args_list[1].args[1]
        assert params["deadline"] - params["detected_at"] == timedelta(hours=72)
        assert params["detected_at"].replace(microsecond=0) == detected.replace(microsecond=0)

    def test_future_detected_at_rejected(self, client):
        db = self._db()
        _as(ADMIN, db)
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        r = client.post("/api/admin/breach", json={"summary": "x" * 5, "detected_at": future})
        assert r.status_code == 422
        db.execute.assert_not_called()

    def test_validation(self, client):
        _as(ADMIN, self._db())
        assert client.post("/api/admin/breach", json={"summary": "ab"}).status_code == 422
        assert (
            client.post(
                "/api/admin/breach", json={"summary": "valid text", "severity": "BOGUS"}
            ).status_code
            == 422
        )

    def test_non_admin_forbidden(self, client):
        db = self._db()
        _as(ENCODER, db)
        assert client.post("/api/admin/breach", json={"summary": "valid text"}).status_code == 403
        db.execute.assert_not_called()

    def test_email_failure_does_not_fail_committed_record(self, client):
        db = self._db()
        _as(ADMIN, db)
        with (
            patch("api.routes.admin.breach.log_system_audit"),
            patch("tasks.notifications.send_email_task") as mail,
        ):
            mail.delay.side_effect = RuntimeError("broker down")
            r = client.post("/api/admin/breach", json={"summary": "valid text"})
        assert r.status_code == 201


# ---------------------------------------------------------------------------
# Anomaly detection no longer feeds threat logs / AI queue
# ---------------------------------------------------------------------------


class TestAnomalyDetachedFromThreatFlow:
    def test_write_anomaly_only_inserts_anomaly_row(self):
        from tasks import anomaly_detection as ad

        db = MagicMock()
        db.execute.return_value.fetchone.return_value = (5,)
        ok = ad._write_anomaly(
            db,
            anomaly_type="OFF_HOURS",
            subject_user_id=ADMIN["user_id"],
            severity="HIGH",
            details={"a": 1},
            dedup_key="k",
            source_ip="1.2.3.4",
        )
        assert ok is True
        assert db.execute.call_count == 1
        assert "anomaly_detections" in str(db.execute.call_args.args[0])
        assert not hasattr(ad, "_push_ai_queue_anomaly")

    def test_dedup_hit_returns_false(self):
        from tasks import anomaly_detection as ad

        db = MagicMock()
        db.execute.return_value.fetchone.return_value = None
        assert (
            ad._write_anomaly(
                db,
                anomaly_type="X",
                subject_user_id=None,
                severity="LOW",
                details={},
                dedup_key="k",
            )
            is False
        )

    def test_detectors_only_read_audit_trails(self):
        src = (
            pathlib.Path(__file__).resolve().parents[1] / "tasks" / "anomaly_detection.py"
        ).read_text(encoding="utf-8")
        assert "suricata_ingestion" not in src and "FROM wims.security_threat_logs" not in src
        assert "INSERT INTO wims.security_threat_logs" not in src


# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------

REMOVED_BEAT = {
    "ingest-suricata-eve",
    "subscribe-suricata-alerts",
    "update-suricata-rules-weekly",
    "process-ai-queue",
    "timeout-pending-civilian-reports",
    "cleanup-orphan-civilian-photos",
    "resync-device-blocklist",
    "expire-community-content",
    "resync-ip-blocklist",
}


class TestCelery:
    def test_beat_schedule_has_no_removed_task(self):
        from celery_config import celery_app

        sched = celery_app.conf.beat_schedule
        assert not (REMOVED_BEAT & set(sched))
        for entry in sched.values():
            t = entry["task"]
            assert not any(
                x in t
                for x in (
                    "suricata",
                    "ai_forwarding",
                    "civilian",
                    "device_blocklist",
                    "ip_blocklist",
                    "expire_content",
                    "report_photos",
                    "routing",
                )
            ), t
        # in-scope jobs survive
        for keep in (
            "detect-behavioral-anomalies",
            "expire-stale-drafts-daily",
            "enforce-password-expiry-daily",
            "refresh-analytics-mvs",
            "execute-scheduled-reports",
            "execute-scheduled-backup",
            "send-weekly-report-email",
            "ensure-pii-key-rotation-daily",
            "worker-heartbeat",
        ):
            assert keep in sched, keep

    def test_removed_task_modules_not_registered(self):
        from celery_config import celery_app

        mods = set(celery_app.conf.imports) | set(celery_app.conf.include or ())
        for m in (
            "tasks.suricata",
            "tasks.suricata_redis",
            "tasks.ai_forwarding",
            "tasks.civilian_reports",
            "tasks.expire_content",
            "tasks.device_blocklist",
            "tasks.ip_blocklist",
            "tasks.report_photos",
            "tasks.routing",
        ):
            assert m not in mods, m

    def test_fcm_removed_email_tasks_kept(self):
        import tasks.notifications as n

        assert not hasattr(n, "send_status_notification") and not hasattr(n, "_get_messaging")
        assert hasattr(n, "send_email_task") and hasattr(n, "send_weekly_report_email")
        assert "firebase" not in pathlib.Path(n.__file__).read_text(
            encoding="utf-8"
        ).lower().replace("(fcm push removed", "")


# ---------------------------------------------------------------------------
# Health payload, config keys, startup, compose
# ---------------------------------------------------------------------------


class TestHealthAndConfig:
    def test_health_payload_has_no_suricata_or_ollama(self, client):
        _as(ADMIN)
        with patch("redis.from_url"), patch("httpx.Client"):
            r = client.get("/api/admin/health")
        assert r.status_code == 200, r.text
        comps = r.json()["components"]
        assert {"database", "redis", "keycloak"} <= set(comps)
        assert "suricata" not in comps and "ollama" not in comps

    @pytest.mark.parametrize(
        "key", ["ai_timeout_seconds", "alert_severity_threshold", "auto_ai_analysis_enabled"]
    )
    def test_hidden_config_keys_cannot_be_patched(self, client, key):
        _as(ADMIN)
        assert client.patch(f"/api/admin/config/{key}", json={"value": "1"}).status_code == 400

    def test_hidden_config_keys_not_listed(self, client):
        db = MagicMock()
        rows = [
            ("ai_timeout_seconds", "60", "x", None, None),
            ("session_timeout_minutes", "30", "y", None, None),
            ("auto_ai_analysis_enabled", "false", "z", None, None),
        ]
        db.execute.return_value.fetchall.return_value = rows
        _as(ADMIN, db)
        keys = [c["key"] for c in client.get("/api/admin/config").json()["config"]]
        assert keys == ["session_timeout_minutes"]

    def test_no_turnstile_startup_requirement(self):
        import main

        assert not hasattr(main, "_require_turnstile_secret_key")
        assert not hasattr(main, "device_token_middleware")

    def test_blocked_ip_check_is_harmless_with_empty_blocklist(self):
        """The request-path check is a Redis EXISTS only: an empty table/keyspace blocks nothing."""
        import asyncio

        import main

        r = MagicMock()

        async def _exists(_k):
            return 0

        r.exists = _exists

        async def _get_redis():
            return r

        async def call_next(_req):
            return "passed"

        req = MagicMock()
        req.url.path = "/api/ref/regions"
        with (
            patch.object(main, "_get_redis", _get_redis),
            patch.object(main, "_get_request_client_ip", lambda _r: "1.2.3.4"),
        ):
            assert asyncio.run(main.blocked_ip_middleware(req, call_next)) == "passed"

    def test_compose_has_no_removed_services_or_references(self):
        import yaml

        root = pathlib.Path(__file__).resolve().parents[2]
        for name in ("docker-compose.yml", "docker-compose.prod.yml"):
            f = root / name
            if not f.exists():
                pytest.skip(f"{name} not mounted")
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
            svcs = doc["services"]
            for gone in ("wims-suricata", "ollama", "ollama-model-pull", "osrm"):
                assert gone not in svcs, (name, gone)
            text_ = f.read_text(encoding="utf-8").lower()
            for needle in (
                "ollama",
                "osrm",
                "suricata",
                "firebase_",
                "turnstile_secret",
                "docker.sock",
                "device_token_signing",
                "civilian_photo",
            ):
                if name == "docker-compose.yml" and needle in ("firebase_",):
                    # frontend NEXT_PUBLIC_FIREBASE_* build args stay until the frontend trim (Phase 4)
                    text_ = "\n".join(
                        ln for ln in text_.splitlines() if "next_public_firebase" not in ln
                    )
                assert needle not in text_, (name, needle)
            for svc in svcs.values():
                deps = svc.get("depends_on") or {}
                assert not ({"ollama", "ollama-model-pull", "osrm", "wims-suricata"} & set(deps))
                assert not any("ollama:" in h or "osrm:" in h for h in svc.get("extra_hosts", []))
