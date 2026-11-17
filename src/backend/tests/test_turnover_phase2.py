"""Client-turnover Phase 2.

Covers:
  * SYSTEM_ADMIN may import AFOR files (region chosen per import) and submit its own
    drafts, but may NOT approve anything (every get_national_validator route -> 403).
  * Encoder import behaviour is unchanged (assigned region wins; mismatch -> 400).
  * Admin-typed temporary password: forwarded to Keycloak only, audit row has no password.
  * 90-day password-expiry task: SYSTEM_ADMIN / NATIONAL_VALIDATOR only, idempotent, audited.
  * Keycloak admin credential env mapping: no admin/admin fallback.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import auth
from database import get_db
from main import app
from services.afor_import.commit import resolve_import_region
from services.afor_import.models import AforParsedRow

ADMIN = {
    "user_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "keycloak_id": "kid-admin",
    "username": "admin",
    "role": "SYSTEM_ADMIN",
}
ENCODER = {
    "user_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "keycloak_id": "kid-encoder",
    "username": "encoder",
    "role": "REGIONAL_ENCODER",
}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_overrides():
    yield
    app.dependency_overrides.clear()


def _as(user: dict, db: MagicMock | None = None):
    app.dependency_overrides[auth.get_current_wims_user] = lambda: dict(user)
    app.dependency_overrides[get_db] = lambda: db or MagicMock()
    app.dependency_overrides[auth.get_db_with_rls] = lambda: db or MagicMock()


def _all_api_routes():
    """Yield (full_path, APIRoute), flattening FastAPI's lazily included routers."""

    def walk(routes, prefix):
        for r in routes:
            if isinstance(r, APIRoute):
                yield prefix + r.path, r
            elif hasattr(r, "original_router"):
                yield from walk(r.original_router.routes, prefix + (r.include_context.prefix or ""))

    yield from walk(app.routes, "")


def _dep_calls(dependant):
    yield dependant.call
    for d in dependant.dependencies:
        yield from _dep_calls(d)


# ---------------------------------------------------------------------------
# Guard: encoder-or-admin
# ---------------------------------------------------------------------------


def _guard(role: str, region):
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = (region,)
    user = {"user_id": "u1", "role": role}
    return asyncio.run(auth.get_encoder_or_admin(user, db))


class TestEncoderOrAdminGuard:
    def test_encoder_allowed_with_region(self):
        assert _guard("REGIONAL_ENCODER", 3)["assigned_region_id"] == 3

    def test_admin_allowed_without_region(self):
        assert _guard("SYSTEM_ADMIN", None)["assigned_region_id"] is None

    @pytest.mark.parametrize(
        "role", ["NATIONAL_VALIDATOR", "NATIONAL_ANALYST", "CIVILIAN_REPORTER", "BOGUS"]
    )
    def test_other_roles_denied(self, role):
        with pytest.raises(HTTPException) as e:
            _guard(role, None)
        assert e.value.status_code == 403

    def test_roles_comment_matches_order(self):
        # Lowest privilege first (fail-safe for multi-role tokens).
        assert auth.WIMS_ROLES_FROM_KEYCLOAK[0] == "CIVILIAN_REPORTER"
        assert auth.WIMS_ROLES_FROM_KEYCLOAK[-1] == "SYSTEM_ADMIN"
        src = open(auth.__file__, encoding="utf-8").read()
        assert "highest first" not in src.lower()


# ---------------------------------------------------------------------------
# Region resolution
# ---------------------------------------------------------------------------


class TestResolveImportRegion:
    def test_admin_requires_region(self):
        with pytest.raises(HTTPException) as e:
            resolve_import_region(MagicMock(), {"role": "SYSTEM_ADMIN"}, None)
        assert e.value.status_code == 400

    def test_admin_unknown_region(self):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = None
        with pytest.raises(HTTPException) as e:
            resolve_import_region(db, {"role": "SYSTEM_ADMIN"}, 999)
        assert e.value.status_code == 400

    def test_admin_valid_region(self):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = (1,)
        assert resolve_import_region(db, {"role": "SYSTEM_ADMIN"}, 5) == 5

    def test_encoder_assigned_region_wins_over_request(self):
        user = {"role": "REGIONAL_ENCODER", "assigned_region_id": 3}
        assert resolve_import_region(MagicMock(), user, 9) == 3

    def test_encoder_without_region_forbidden(self):
        with pytest.raises(HTTPException) as e:
            resolve_import_region(MagicMock(), {"role": "REGIONAL_ENCODER", "assigned_region_id": None}, None)
        assert e.value.status_code == 403


# ---------------------------------------------------------------------------
# AFOR import route
# ---------------------------------------------------------------------------


def _rows(region_text="Region III - Central Luzon"):
    return [
        AforParsedRow(
            row_index=0, status="VALID", errors=[], data={"_region_text": region_text, "region_id": 5}
        )
    ]


def _post_import(client, data=None):
    return client.post(
        "/api/regional/afor/import",
        files={"file": ("a.xlsx", b"PK\x03\x04x", "application/octet-stream")},
        data=data or {},
    )


class TestAforImportRoute:
    def _patches(self, region_text):
        return (
            patch(
                "api.routes.regional.afor._read_validated_upload",
                return_value=(b"x", "xlsx"),
            ),
            patch(
                "api.routes.regional.afor._parse_rows",
                return_value=(_rows(region_text), "STRUCTURAL_AFOR"),
            ),
            patch("api.routes.regional.afor.log_system_audit"),
        )

    def test_admin_without_region_is_400(self, client):
        _as(ADMIN)
        p1, p2, p3 = self._patches("Region III - Central Luzon")
        with p1, p2, p3:
            r = _post_import(client)
        assert r.status_code == 400
        assert "region_id" in r.json()["detail"]

    def test_admin_mismatch_warns_allows_and_audits(self, client):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = ("National Capital Region",)
        _as(ADMIN, db)
        p1, p2, p3 = self._patches("Region III - Central Luzon")
        with p1, p2, p3 as audit:
            r = _post_import(client, {"region_id": "1"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["region_mismatch"] is True
        assert body["region_id"] == 1
        assert body["file_region_text"] == "Region III - Central Luzon"
        nv = audit.call_args.kwargs["new_values"]
        assert nv["actor_role"] == "SYSTEM_ADMIN"
        assert nv["chosen_region_id"] == 1
        assert nv["file_region_text"] == "Region III - Central Luzon"
        assert nv["region_mismatch"] is True

    def test_admin_matching_region_no_warning(self, client):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = ("Region III - Central Luzon",)
        _as(ADMIN, db)
        p1, p2, p3 = self._patches("Region III - Central Luzon")
        with p1, p2, p3:
            r = _post_import(client, {"region_id": "5"})
        assert r.status_code == 200
        assert r.json()["region_mismatch"] is False

    def test_encoder_mismatch_still_rejected(self, client):
        db = MagicMock()
        # guard lookup -> assigned region 1; region-name lookup -> NCR
        db.execute.return_value.fetchone.return_value = (1,)
        _as(ENCODER, db)
        p1, p2, p3 = self._patches("Region III - Central Luzon")
        with p1, p2, p3, patch(
            "api.routes.regional.afor.text", side_effect=lambda s: s
        ):
            db.execute.return_value.fetchone.side_effect = [(1,), ("National Capital Region",)]
            r = _post_import(client)
        assert r.status_code == 400
        assert "Region mismatch" in r.json()["detail"]

    @pytest.mark.parametrize("role", ["NATIONAL_VALIDATOR", "NATIONAL_ANALYST"])
    def test_other_roles_forbidden(self, client, role):
        _as({**ENCODER, "role": role})
        p1, p2, p3 = self._patches("x")
        with p1, p2, p3:
            assert _post_import(client).status_code == 403


# ---------------------------------------------------------------------------
# Approval stays validator-only
# ---------------------------------------------------------------------------


def _validator_guarded_mutations():
    out = []
    for path, route in _all_api_routes():
        if auth.get_national_validator in list(_dep_calls(route.dependant)):
            for m in route.methods - {"GET", "HEAD", "OPTIONS"}:
                out.append((m, path))
    return out


class TestAdminCannotApprove:
    def test_there_are_validator_mutation_routes(self):
        assert len(_validator_guarded_mutations()) >= 5

    def test_admin_gets_403_on_every_validator_mutation(self, client):
        _as(ADMIN)
        failures = []
        for method, path in _validator_guarded_mutations():
            url = re.sub(r"\{[^}]+\}", "1", path)
            resp = client.request(method, url, json={})
            if resp.status_code != 403:
                failures.append((method, path, resp.status_code))
        assert not failures, failures

    def test_no_approval_route_uses_the_new_guard(self):
        for path, route in _all_api_routes():
            calls = list(_dep_calls(route.dependant))
            if auth.get_encoder_or_admin in calls:
                assert auth.get_national_validator not in calls
                assert "verification" not in path
                assert "approve" not in path

    def test_new_guard_only_on_afor_and_submit(self):
        used = sorted(
            path
            for path, route in _all_api_routes()
            if auth.get_encoder_or_admin in list(_dep_calls(route.dependant))
        )
        assert used == [
            "/api/regional/afor/commit",
            "/api/regional/afor/detect-region",
            "/api/regional/afor/import",
            "/api/regional/incidents/{incident_id}/submit",
        ]

    def test_other_encoder_only_routes_still_deny_admin(self, client):
        _as(ADMIN)
        # create / update drafts stay encoder-only
        assert client.post("/api/regional/incidents", json={}).status_code == 403
        assert client.delete("/api/regional/incidents/draft/1").status_code == 403


# ---------------------------------------------------------------------------
# Admin-set temporary password
# ---------------------------------------------------------------------------

KC_ID = "0f6a4c3e-1111-4222-8333-944455556666"
SECRET = "Tmp-Pa55word!xyz"


def _db_with_user():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = (
        "c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "target.user",
        "REGIONAL_ENCODER",
    )
    return db


class TestTemporaryPassword:
    def test_sets_temporary_and_audit_has_no_password(self, client):
        _as(ADMIN, _db_with_user())
        with (
            patch("api.routes.admin.users.set_temporary_password") as kc,
            patch("api.routes.admin.users.log_system_audit") as audit,
        ):
            r = client.post(
                f"/api/admin/users/{KC_ID}/temporary-password", json={"temporary_password": SECRET}
            )
        assert r.status_code == 200, r.text
        kc.assert_called_once_with(KC_ID, SECRET)
        assert SECRET not in r.text
        assert r.json()["must_change_at_first_login"] is True
        assert audit.call_count == 1
        kwargs = audit.call_args.kwargs
        assert kwargs["action_type"] == "SET_TEMPORARY_PASSWORD"
        assert kwargs["user_id"] == ADMIN["user_id"]
        assert SECRET not in repr(kwargs)
        assert "password" not in {k.lower() for k in kwargs["new_values"]}
        assert kwargs["new_values"]["target_username"] == "target.user"

    def test_policy_rejection_is_422_audited_and_not_echoed(self, client):
        from keycloak.exceptions import KeycloakError

        _as(ADMIN, _db_with_user())
        err = KeycloakError(f'400: {{"error":"password_policy","error_description":"Invalid password: {SECRET}"}}')
        with (
            patch("api.routes.admin.users.set_temporary_password", side_effect=err),
            patch("api.routes.admin.users.log_system_audit") as audit,
        ):
            r = client.post(
                f"/api/admin/users/{KC_ID}/temporary-password", json={"temporary_password": SECRET}
            )
        assert r.status_code == 422
        assert SECRET not in r.text
        assert audit.call_args.kwargs["result"] == "failure"
        assert SECRET not in repr(audit.call_args.kwargs)

    def test_short_password_rejected_before_keycloak(self, client):
        _as(ADMIN, _db_with_user())
        with patch("api.routes.admin.users.set_temporary_password") as kc:
            r = client.post(
                f"/api/admin/users/{KC_ID}/temporary-password", json={"temporary_password": "short"}
            )
        assert r.status_code == 422
        kc.assert_not_called()

    def test_unknown_user_404(self, client):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = None
        _as(ADMIN, db)
        with patch("api.routes.admin.users.set_temporary_password") as kc:
            r = client.post(
                f"/api/admin/users/{KC_ID}/temporary-password", json={"temporary_password": SECRET}
            )
        assert r.status_code == 404
        kc.assert_not_called()

    def test_non_admin_forbidden(self, client):
        _as(ENCODER)
        with patch("api.routes.admin.users.set_temporary_password") as kc:
            r = client.post(
                f"/api/admin/users/{KC_ID}/temporary-password", json={"temporary_password": SECRET}
            )
        assert r.status_code == 403
        kc.assert_not_called()

    def test_service_marks_credential_temporary(self):
        import services.keycloak_admin as ka

        adm = MagicMock()
        with patch.object(ka, "_get_admin_client", return_value=adm):
            ka.set_temporary_password(KC_ID, SECRET)
        adm.set_user_password.assert_called_once_with(user_id=KC_ID, password=SECRET, temporary=True)
        adm.user_logout.assert_called_once_with(user_id=KC_ID)


# ---------------------------------------------------------------------------
# Keycloak admin credentials: no admin/admin fallback
# ---------------------------------------------------------------------------


class TestKeycloakAdminCredentials:
    def test_missing_credentials_fail_clearly(self, monkeypatch):
        import services.keycloak_admin as ka

        for k in ("KEYCLOAK_ADMIN_USER", "KEYCLOAK_ADMIN", "KEYCLOAK_ADMIN_PASSWORD"):
            monkeypatch.delenv(k, raising=False)
        with pytest.raises(RuntimeError, match="KEYCLOAK_ADMIN_PASSWORD"):
            ka._kc_admin_credentials()

    def test_password_alone_is_not_enough(self, monkeypatch):
        import services.keycloak_admin as ka

        for k in ("KEYCLOAK_ADMIN_USER", "KEYCLOAK_ADMIN"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "x")
        with pytest.raises(RuntimeError):
            ka._kc_admin_credentials()

    def test_keycloak_admin_alias_accepted(self, monkeypatch):
        import services.keycloak_admin as ka

        monkeypatch.delenv("KEYCLOAK_ADMIN_USER", raising=False)
        monkeypatch.setenv("KEYCLOAK_ADMIN", "kcroot")
        monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "s3cret-non-default")
        assert ka._kc_admin_credentials() == ("kcroot", "s3cret-non-default")

    def test_explicit_user_wins(self, monkeypatch):
        import services.keycloak_admin as ka

        monkeypatch.setenv("KEYCLOAK_ADMIN_USER", "u1")
        monkeypatch.setenv("KEYCLOAK_ADMIN", "u2")
        monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "p")
        assert ka._kc_admin_credentials()[0] == "u1"

    def test_client_authenticates_with_env_values(self, monkeypatch):
        import services.keycloak_admin as ka

        monkeypatch.setenv("KEYCLOAK_ADMIN_USER", "kcroot")
        monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "s3cret-non-default")
        with patch.object(ka, "KeycloakOpenID") as oidc, patch.object(ka, "KeycloakAdmin"):
            ka._get_admin_client()
        oidc.return_value.token.assert_called_once_with("kcroot", "s3cret-non-default")

    def test_compose_wires_admin_env_for_backend_and_celery(self):
        import pathlib

        import yaml

        compose = pathlib.Path(__file__).resolve().parents[2] / "docker-compose.yml"
        if not compose.exists():
            pytest.skip("docker-compose.yml not mounted in this environment")
        services = yaml.safe_load(compose.read_text(encoding="utf-8"))["services"]
        for name in ("backend", "celery-worker"):
            env = services[name]["environment"]
            flat = "\n".join(env) if isinstance(env, list) else "\n".join(f"{k}={v}" for k, v in env.items())
            assert "KEYCLOAK_ADMIN_USER=" in flat, name
            assert "KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:?error}" in flat, name


# ---------------------------------------------------------------------------
# 90-day password expiry task
# ---------------------------------------------------------------------------

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)


def _ms(days_ago: float) -> int:
    return int((NOW - timedelta(days=days_ago)).timestamp() * 1000)


class TestPasswordAge:
    def test_age_and_boundaries(self):
        from tasks.password_expiry import is_password_expired, password_age_days

        assert password_age_days(None, NOW) is None
        assert round(password_age_days(_ms(91), NOW)) == 91
        assert is_password_expired(_ms(91), 90, NOW)
        assert not is_password_expired(_ms(89), 90, NOW)
        assert not is_password_expired(_ms(90), 90, NOW)  # exactly 90 days: not yet older
        assert not is_password_expired(None, 90, NOW)


class TestEnforcePasswordExpiry:
    def _run(self, members_by_role, added=None):
        import tasks.password_expiry as pe

        added = added if added is not None else []

        def fake_list(role):
            return members_by_role.get(role, [])

        def fake_add(kid, action):
            added.append((kid, action))
            return True

        session = MagicMock()
        with (
            patch.object(pe, "list_role_members_with_password_age", side_effect=fake_list) as lst,
            patch.object(pe, "add_required_action", side_effect=fake_add),
            patch.object(pe, "_AdminSessionLocal", return_value=session),
            patch.object(pe, "set_rls_context"),
            patch.object(pe, "log_system_audit") as audit,
            patch.object(pe, "datetime") as dt,
        ):
            dt.now.return_value = NOW
            dt.fromtimestamp = datetime.fromtimestamp
            summary = pe.enforce_password_expiry()
        return summary, added, audit, lst

    def member(self, kid, name, days, actions=(), enabled=True):
        return {
            "id": kid,
            "username": name,
            "enabled": enabled,
            "required_actions": list(actions),
            "password_created_ms": _ms(days) if days is not None else None,
        }

    def test_flags_only_old_admin_and_validator_and_audits(self):
        summary, added, audit, lst = self._run(
            {
                "SYSTEM_ADMIN": [self.member("a1", "old.admin", 120), self.member("a2", "new.admin", 10)],
                "NATIONAL_VALIDATOR": [self.member("v1", "old.validator", 91)],
            }
        )
        assert sorted(added) == [("a1", "UPDATE_PASSWORD"), ("v1", "UPDATE_PASSWORD")]
        assert sorted(summary["flagged"]) == ["old.admin", "old.validator"]
        assert audit.call_count == 2
        nv = audit.call_args_list[0].kwargs["new_values"]
        assert nv["max_age_days"] == 90 and nv["required_action_added"] == "UPDATE_PASSWORD"
        assert nv["password_age_days"] > 90
        assert "password_created_at" in nv
        # only the two privileged roles are ever queried: encoders / analysts untouched
        assert [c.args[0] for c in lst.call_args_list] == ["SYSTEM_ADMIN", "NATIONAL_VALIDATOR"]

    def test_idempotent_already_flagged_and_disabled_and_unknown_date(self):
        summary, added, audit, _ = self._run(
            {
                "SYSTEM_ADMIN": [
                    self.member("a1", "flagged", 200, actions=["UPDATE_PASSWORD"]),
                    self.member("a2", "disabled", 200, enabled=False),
                    self.member("a3", "nodate", None),
                ]
            }
        )
        assert added == []
        assert audit.call_count == 0
        assert summary["already_flagged"] == 1
        assert summary["flagged"] == []

    def test_keycloak_failure_is_counted_not_fatal(self):
        import tasks.password_expiry as pe

        session = MagicMock()
        with (
            patch.object(pe, "list_role_members_with_password_age", side_effect=RuntimeError("kc down")),
            patch.object(pe, "_AdminSessionLocal", return_value=session),
            patch.object(pe, "set_rls_context"),
            patch.object(pe, "log_system_audit") as audit,
        ):
            summary = pe.enforce_password_expiry()
        assert summary["errors"] == 2
        assert audit.call_count == 0

    def test_scheduled_daily_and_registered(self):
        from celery_config import celery_app

        entry = celery_app.conf.beat_schedule["enforce-password-expiry-daily"]
        assert entry["task"] == "tasks.password_expiry.enforce_password_expiry"
        assert "tasks.password_expiry" in celery_app.conf.imports
        assert set(__import__("tasks.password_expiry", fromlist=["x"]).EXPIRY_ROLES) == {
            "SYSTEM_ADMIN",
            "NATIONAL_VALIDATOR",
        }


class TestPasswordAgeFromKeycloak:
    def test_picks_newest_password_credential(self):
        import services.keycloak_admin as ka

        adm = MagicMock()
        adm.get_realm_role_members.return_value = [
            {"id": "u1", "username": "x", "enabled": True, "requiredActions": []}
        ]
        adm.get_credentials.return_value = [
            {"type": "otp", "createdDate": 9_999_999_999_999},
            {"type": "password", "createdDate": 1000},
            {"type": "password", "createdDate": 5000},
        ]
        with patch.object(ka, "_get_admin_client", return_value=adm):
            out = ka.list_role_members_with_password_age("SYSTEM_ADMIN")
        assert out[0]["password_created_ms"] == 5000

    def test_add_required_action_is_idempotent(self):
        import services.keycloak_admin as ka

        adm = MagicMock()
        adm.get_user.return_value = {"requiredActions": ["UPDATE_PASSWORD"]}
        with patch.object(ka, "_get_admin_client", return_value=adm):
            assert ka.add_required_action("u1", "UPDATE_PASSWORD") is False
        adm.update_user.assert_not_called()
        adm.get_user.return_value = {"requiredActions": ["CONFIGURE_TOTP"]}
        with patch.object(ka, "_get_admin_client", return_value=adm):
            assert ka.add_required_action("u1", "UPDATE_PASSWORD") is True
        adm.update_user.assert_called_once_with(
            user_id="u1", payload={"requiredActions": ["CONFIGURE_TOTP", "UPDATE_PASSWORD"]}
        )
