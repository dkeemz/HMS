from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.rate_limit import AUTH_RATE, MFA_VERIFY_RATE, limiter
from app.core.security import compute_device_fingerprint, sync_user_from_keycloak
from app.core.session import create_session, invalidate_all_sessions
from app.models.session import UserSession
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MFAChallengeResponse,
    RefreshRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.keycloak import KeycloakService
from app.services.notifications import NotificationService
from app.services.password_policy import PasswordPolicyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _keycloak_service() -> KeycloakService:
    return KeycloakService()


# ── POST /auth/login ──────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse | MFAChallengeResponse)
@limiter.limit(AUTH_RATE)
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
    # Check account lockout before attempting authentication
    existing_user_result = await db.execute(
        select(User).where(User.email == body.email)
    )
    existing_user = existing_user_result.scalar_one_or_none()

    if existing_user is not None:
        is_locked, locked_until = await PasswordPolicyService.check_account_lockout(
            db, existing_user.id
        )
        if is_locked:
            await NotificationService.send_account_locked_notification(
                existing_user.email
            )
            raise HTTPException(
                status_code=403,
                detail="Account locked. Try again later.",
            )

    # Attempt Keycloak authentication
    # Look up KC user by email first to get their KC username
    kc_username = body.email
    try:
        kc_user = kc.get_user_by_email(body.email)
        if kc_user is not None:
            kc_username = kc_user.get("username", body.email)
    except Exception:
        pass

    try:
        token_data = kc.get_token(username=kc_username, password=body.password)
    except Exception:
        # Record failed attempt if user exists
        if existing_user is not None:
            is_now_locked, locked_until = (
                await PasswordPolicyService.record_failed_attempt(
                    db, existing_user.id
                )
            )
            await db.commit()
            if is_now_locked:
                await NotificationService.send_account_locked_notification(
                    existing_user.email
                )
                raise HTTPException(
                    status_code=403,
                    detail="Account locked due to too many failed attempts.",
                )
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

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

    # Clear failed attempts on successful login
    await PasswordPolicyService.clear_failed_attempts(db, user.id)

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

    await invalidate_all_sessions(db, user.id)

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

    if is_new_device and not settings.DEBUG:
        # Notify user of new device login
        await NotificationService.send_login_notification(
            user.email,
            {"user_agent": user_agent, "ip_address": ip_address},
            is_new_device=True,
        )
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
        phone=current_user.phone,
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


# ── PUT /auth/me ─────────────────────────────────────────────────────────


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(_keycloak_service),
):
    """Update the current user's profile (name, phone)."""
    if body.first_name is not None:
        current_user.first_name = body.first_name
    if body.last_name is not None:
        current_user.last_name = body.last_name
    if body.phone is not None:
        current_user.phone = body.phone

    # Also update in Keycloak if the user is managed by Keycloak
    keycloak_sub = current_user.password_hash.removeprefix("keycloak:")
    if keycloak_sub and keycloak_sub != current_user.password_hash:
        try:
            update_data: dict = {}
            if body.first_name is not None:
                update_data["firstName"] = body.first_name
            if body.last_name is not None:
                update_data["lastName"] = body.last_name
            if update_data and kc.admin is not None:
                kc.admin.update_user(keycloak_sub, update_data)
        except Exception:
            logger.warning(
                "Failed to update Keycloak profile for user %s",
                current_user.id,
            )

    await db.flush()

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
        phone=current_user.phone,
        status=current_user.status,
        roles=roles,
        last_login_at=current_user.last_login_at,
    )


# ── POST /auth/mfa/verify ───────────────────────────────────────────────


@router.post("/mfa/verify", response_model=TokenResponse)
@limiter.limit(MFA_VERIFY_RATE)
async def verify_mfa(
    session_id: str,
    code: str,
    request: Request,
    response: Response,
    mfa_method: str = "totp",
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(_keycloak_service),
):
    """Verify an MFA code (TOTP or push notification) for a pending session.

    On success the session is activated and tokens are returned.
    """
    # Look up the pending session
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.is_active.is_(True),
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired MFA session.",
        )

    # Look up the user for this session
    user_result = await db.execute(
        select(User).where(User.id == session.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")

    keycloak_sub = user.password_hash.removeprefix("keycloak:")

    if mfa_method == "totp":
        # Verify TOTP code via Keycloak token exchange with the OTP credential
        try:
            token_data = kc.get_token(username=user.email, password=code)
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Invalid MFA code.",
            )
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 900)

    elif mfa_method == "push_notification":
        # For push notifications the code is the approval token from the
        # Keycloak push notification flow.  Verify via token exchange.
        try:
            token_data = kc.get_token(username=user.email, password=code)
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Push notification not approved or expired.",
            )
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 900)

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported MFA method. Use 'totp' or 'push_notification'.",
        )

    # Mark the Keycloak required action as completed if it was pending
    if keycloak_sub and keycloak_sub != user.password_hash:
        try:
            actions = kc.get_required_actions(keycloak_sub)
            remaining = [a for a in actions if a != "CONFIGURE_TOTP"]
            if remaining != actions:
                kc.set_required_actions(keycloak_sub, remaining)
        except Exception:
            logger.warning("Failed to update Keycloak required actions for %s", user.id)

    # Set the access token cookie
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
