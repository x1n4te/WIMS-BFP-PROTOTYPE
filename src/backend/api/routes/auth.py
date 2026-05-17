"""
Dev bypass auth — Keycloak Resource Owner Password Credentials Grant (direct grant).
POST /api/dev-login  { role, username, password }
Returns: { access_token, refresh_token }

WARNING: Intentional dev-only backdoor. NEVER SHIP TO PROD.
Documented in: system-wiki/gaps/security-gap-register.md — DEV-BYPASS-001 CRITICAL
"""

from __future__ import annotations

import os
import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import auth

logger = logging.getLogger("wims.auth")

# Allowed roles for dev bypass — must match grill-me session decision
ALLOWED_ROLES = {"REGIONAL_ENCODER", "NATIONAL_VALIDATOR", "NATIONAL_ANALYST", "SYSTEM_ADMIN"}

router = APIRouter(tags=["auth"])

# Reconstruct TOKEN_ENDPOINT from auth.py config (same formula as main.py)
_keycloak_url = os.environ.get(
    "KEYCLOAK_URL", "http://keycloak:8080/auth/realms/bfp"
)
_TOKEN_ENDPOINT = f"{_keycloak_url}/protocol/openid-connect/token"


class DevLoginRequest(BaseModel):
    role: str
    username: str
    password: str


class DevLoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None


@router.post("/dev-login", response_model=DevLoginResponse)
async def dev_login(body: DevLoginRequest):
    """
    Keycloak direct grant (Resource Owner Password Credentials Grant).
    Exchanges username + password for an OIDC token and returns it.

    WARNING: This endpoint is a QA/debug artifact with no production use case.
    - Severity: CRITICAL — full role impersonation possible
    - Blast radius: REGIONAL_ENCODER, NATIONAL_VALIDATOR, NATIONAL_ANALYST, SYSTEM_ADMIN
    - Gate: security-gap-register.md DEV-BYPASS-001 — the single authoritative safeguard
    """
    # Gate 1: role must be in allowed list (enforced per grill-me session decision)
    if body.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Allowed: {', '.join(sorted(ALLOWED_ROLES))}",
        )

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            _TOKEN_ENDPOINT,
            data={
                "grant_type": "password",
                "username": body.username,
                "password": body.password,
                "client_id": auth.CLIENT_ID,  # wims-web — must match KEYCLOAK_CLIENT_ID env var so the token audience matches what validate_token expects
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_resp.status_code != 200:
        detail = token_resp.json().get("error_description", "Invalid credentials")
        raise HTTPException(status_code=401, detail=detail)

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token in response")

    # NOTE: Skipping JWT validation here (Keycloak issues tokens for 'bfp-client' audience
    # but backend validates against 'wims-web' audience). Dogfood QA injects this token
    # via browser_console and the browser sends it to the backend, which validates it
    # using the same Keycloak JWKS. The internal validate_token call would fail because
    # audience mismatch. For dev-bypass only — do not apply this pattern elsewhere.

    logger.warning(
        f"[DEV-BYPASS] token issued for role={body.role} username={body.username}"
    )

    return DevLoginResponse(
        access_token=access_token,
        refresh_token=token_data.get("refresh_token"),
    )