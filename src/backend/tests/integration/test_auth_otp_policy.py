"""Source-inspection tests for the turnover realm's MFA / password policy.

They read ``keycloak/import/bfp-realm.json`` (the realm compose imports) and do
not need a running Keycloak.
"""

import json
from pathlib import Path

IMPORT_REALM_PATH = Path(__file__).resolve().parents[3] / "keycloak" / "import" / "bfp-realm.json"


def _load_import_realm() -> dict:
    with IMPORT_REALM_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _flow_by_alias(realm: dict, alias: str) -> dict:
    for flow in realm.get("authenticationFlows", []):
        if flow.get("alias") == alias:
            return flow
    raise AssertionError(f"Authentication flow not found: {alias}")


def _auth_config_by_alias(realm: dict, alias: str) -> dict:
    for cfg in realm.get("authenticatorConfig", []):
        if cfg.get("alias") == alias:
            return cfg
    raise AssertionError(f"Authenticator config not found: {alias}")


def _otp_subflow_role(realm: dict, flow_alias: str) -> str:
    """Return the role a conditional OTP sub-flow is gated on, asserting its shape."""
    flow = _flow_by_alias(realm, flow_alias)
    execs = flow["authenticationExecutions"]
    cond = [e for e in execs if e.get("authenticator") == "conditional-user-role"]
    otp = [e for e in execs if e.get("authenticator") == "auth-otp-form"]
    assert len(cond) == 1 and cond[0]["requirement"] == "REQUIRED"
    assert len(otp) == 1 and otp[0]["requirement"] == "REQUIRED"
    cfg = _auth_config_by_alias(realm, cond[0]["authenticatorConfig"])
    assert cfg["config"].get("negate") == "false"
    return cfg["config"]["condUserRole"]


def test_forms_flow_requires_otp_only_for_admin_and_validator():
    realm = _load_import_realm()
    forms = _flow_by_alias(realm, "forms")
    execs = forms["authenticationExecutions"]

    assert execs[0]["authenticator"] == "auth-username-password-form"
    assert execs[0]["requirement"] == "REQUIRED"

    subflows = {e["flowAlias"]: e for e in execs if e.get("authenticatorFlow")}
    assert set(subflows) == {"Browser - Admin OTP", "Browser - Validator OTP"}
    assert all(e["requirement"] == "CONDITIONAL" for e in subflows.values())

    assert _otp_subflow_role(realm, "Browser - Admin OTP") == "SYSTEM_ADMIN"
    assert _otp_subflow_role(realm, "Browser - Validator OTP") == "NATIONAL_VALIDATOR"


def test_no_demo_otp_provider_or_skip_mfa_bypass():
    realm = _load_import_realm()
    text = json.dumps(realm)
    assert "wims-demo-otp-form" not in text
    assert "SKIP_MFA" not in text
    assert "otp-skip-mfa" not in text
    assert "SKIP_MFA" not in {r["name"] for r in realm["roles"]["realm"]}


def test_configure_totp_is_not_a_default_action():
    """Encoders/analysts must not be forced to enrol OTP on first login."""
    realm = _load_import_realm()
    totp = next(a for a in realm["requiredActions"] if a["alias"] == "CONFIGURE_TOTP")
    assert totp["enabled"] is True
    assert totp["defaultAction"] is False


def test_direct_grant_otp_is_conditional_on_user_having_otp():
    """bfp-client password verification must not fail for users without OTP."""
    realm = _load_import_realm()
    dg = _flow_by_alias(realm, "direct grant")
    cond_execs = [
        e for e in dg["authenticationExecutions"] if e.get("flowAlias") == "Direct Grant - Conditional OTP"
    ]
    assert len(cond_execs) == 1 and cond_execs[0]["requirement"] == "CONDITIONAL"
    assert "direct-grant-validate-otp" not in {
        e.get("authenticator") for e in dg["authenticationExecutions"]
    }
    sub = _flow_by_alias(realm, "Direct Grant - Conditional OTP")
    auths = {e["authenticator"]: e["requirement"] for e in sub["authenticationExecutions"]}
    assert auths == {
        "conditional-user-configured": "REQUIRED",
        "direct-grant-validate-otp": "REQUIRED",
    }


def test_password_and_reset_link_policy():
    realm = _load_import_realm()
    policy = realm["passwordPolicy"]
    for token in (
        "length(12)",
        "upperCase(1)",
        "lowerCase(1)",
        "digits(1)",
        "specialChars(1)",
        "passwordHistory(3)",
    ):
        assert token in policy
    assert realm["actionTokenGeneratedByUserLifespan"] == 900  # 15 min reset link
    assert realm["ssoSessionIdleTimeout"] == 1800
    assert realm["ssoSessionMaxLifespan"] == 28800
    assert realm["bruteForceProtected"] is True
    assert realm["failureFactor"] == 5


def test_turnover_realm_ships_no_seed_users():
    realm = _load_import_realm()
    assert realm["users"] == []
