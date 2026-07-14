from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.security import compute_device_fingerprint, sync_user_from_keycloak
from app.core.session import create_session, invalidate_all_sessions
from app.models.session import UserSession
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MFAChallengeResponse,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.keycloak import KeycloakService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _keycloak_service() -> KeycloakService:
    return KeycloakService()


# ── POST /auth/login ──────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse | MFAChallengeResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(_keycloak_service),
):
    """Authenticate with email + password via Keycloak.

    Returns tokens on success, or an MFA challenge if the user's device
    fingerprint is new (conditional MFA enforcement).
    """
    token_data = kc.get_token(username=body.email, password=body.password)

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data.get("expires_in", 900)

    user_info = kc.get_user_info(access_token)
    keycloak_sub = user_info.get("sub", "")

    # Sync user into HMS
    payload = {
        "sub": keycloak_sub,
        "email": user_info.get("email", body.email),
        "given_name": user_info.get("given_name", ""),
        "family_name": user_info.get("family_name", ""),
    }
    user = await sync_user_from_keycloak(db, payload)
    user.last_login_at = datetime.now(UTC)
    await db.flush()

    # Device fingerprint for conditional MFA
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else ""
    fingerprint = compute_device_fingerprint(user_agent, ip_address)

    known = await db.execute(
        select(UserSession.id).where(
            UserSession.user_id == user.id,
            UserSession.device_fingerprint == fingerprint,
            UserSession.is_active.is_(True),
        )
    )
    is_new_device = known.scalar_one_or_none() is None

    session = await create_session(
        db,
        user_id=user.id,
        device_info={"user_agent": user_agent},
        ip_address=ip_address,
        user_agent=user_agent,
        device_fingerprint=fingerprint,
        keycloak_session_id=keycloak_sub,
    )
    await db.commit()

    if is_new_device:
        # Prompt for MFA on new device
        return MFAChallengeResponse(
            session_id=str(session.id),
            mfa_required=True,
            mfa_methods=["push_notification", "totp"],
        )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        max_age=expires_in,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        session_id=str(session.id),
    )


# ── POST /auth/logout ─────────────────────────────────────────────────────


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    response: Response,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(_keycloak_service),
):
    """Revoke the Keycloak refresh token and clear the session cookie."""
    try:
        kc.logout(body.refresh_token)
    except Exception:
        logger.warning("Keycloak logout failed (token may already be expired)")

    await invalidate_all_sessions(db, current_user.id)
    await db.commit()

    response.delete_cookie("access_token")
    return {"message": "Logged out"}


# ── POST /auth/refresh ────────────────────────────────────────────────────


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(_keycloak_service),
):
    """Obtain a new access token using a Keycloak refresh token."""
    token_data = kc.refresh_token(body.refresh_token)

    access_token = token_data["access_token"]
    new_refresh_token = token_data.get("refresh_token", body.refresh_token)
    expires_in = token_data.get("expires_in", 900)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        max_age=expires_in,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
        session_id="",
    )


# ── GET /auth/me ──────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's profile and roles."""
    from app.models.role import Role
    from app.models.user_role import UserRole

    result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    roles = [row[0] for row in result.all()]

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        status=current_user.status,
        roles=roles,
        last_login_at=current_user.last_login_at,
    )


# ── GET /auth/mfa-status ──────────────────────────────────────────────────


@router.get("/mfa-status")
async def mfa_status(
    current_user: CurrentUser,
    kc: KeycloakService = Depends(_keycloak_service),
):
    """Check whether the current user has MFA configured in Keycloak."""
    # The password_hash field stores keycloak:<sub> for Keycloak-managed users
    keycloak_sub = current_user.password_hash.replace("keycloak:", "")
    try:
        actions = kc.get_required_actions(keycloak_sub)
        return {
            "mfa_configured": "CONFIGURE_TOTP" not in actions,
            "pending_actions": actions,
        }
    except Exception:
        return {"mfa_configured": False, "pending_actions": []}
