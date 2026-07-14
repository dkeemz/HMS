from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.session import invalidate_all_sessions
from app.models.user import User
from app.schemas.password import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordValidateRequest,
    PasswordValidateResponse,
)
from app.services.keycloak import KeycloakService
from app.services.notifications import NotificationService
from app.services.password_policy import PasswordPolicyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/password", tags=["password"])


@router.post("/validate", response_model=PasswordValidateResponse)
async def validate_password_endpoint(body: PasswordValidateRequest):
    """Validate a password against the HMS policy."""
    is_valid, message = PasswordPolicyService.validate_password(body.password)
    return PasswordValidateResponse(
        valid=is_valid,
        message=message if not is_valid else "Password meets policy requirements",
        errors=[message] if not is_valid else [],
    )


@router.post("/reset-request", response_model=PasswordResetResponse)
async def request_password_reset(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(KeycloakService),
):
    """Request a password reset (sends email with token)."""
    # Look up user by email — silently succeed even if not found (don't leak existence)
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        token = await PasswordPolicyService.generate_reset_token(db, user.id)
        await NotificationService.send_password_reset_email(user.email, token)
        await db.commit()

    return PasswordResetResponse(
        message="If an account with that email exists, a reset link has been sent"
    )


@router.post("/reset-confirm", response_model=PasswordChangeResponse)
async def confirm_password_reset(
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(KeycloakService),
):
    """Confirm a password reset with the token from email."""
    user_id = await PasswordPolicyService.validate_reset_token(db, body.token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Validate new password policy
    is_valid, message = PasswordPolicyService.validate_password(body.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # Check password history
    import bcrypt

    new_hash = bcrypt.hashpw(
        body.new_password.encode(), bcrypt.gensalt()
    ).decode()

    history_ok = await PasswordPolicyService.check_password_history(
        db, user_id, new_hash
    )
    if not history_ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password was recently used. Please choose a different password.",
        )

    # Update password in Keycloak
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    keycloak_sub = user.password_hash.removeprefix("keycloak:")
    if keycloak_sub and keycloak_sub != user.password_hash:
        try:
            if kc.admin is not None:
                kc.admin.set_user_password(
                    keycloak_sub, body.new_password, temporary=False
                )
        except Exception:
            logger.exception("Failed to update Keycloak password for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password in identity provider",
            )

    # Record in password history
    await PasswordPolicyService.record_password_usage(db, user_id, new_hash)

    # Mark token as used
    await PasswordPolicyService.mark_token_used(db, body.token)

    # Update password age
    from datetime import UTC, datetime

    from sqlalchemy import update

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(password_last_changed_at=datetime.now(UTC))
    )

    # Invalidate all sessions
    await invalidate_all_sessions(db, user_id)

    # Send notification
    await NotificationService.send_password_changed_notification(user.email)

    await db.commit()

    return PasswordChangeResponse(message="Password reset successfully")


@router.post("/change", response_model=PasswordChangeResponse)
async def change_password(
    body: PasswordChangeRequest,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(KeycloakService),
):
    """Change password (requires current password verification via Keycloak)."""
    # Verify current password by attempting Keycloak token exchange
    try:
        token_data = kc.get_token(
            username=current_user.email, password=body.current_password
        )
        if "access_token" not in token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Validate new password policy
    is_valid, message = PasswordPolicyService.validate_password(body.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # Check password history
    import bcrypt

    new_hash = bcrypt.hashpw(
        body.new_password.encode(), bcrypt.gensalt()
    ).decode()

    history_ok = await PasswordPolicyService.check_password_history(
        db, current_user.id, new_hash
    )
    if not history_ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password was recently used. Please choose a different password.",
        )

    # Update password in Keycloak
    keycloak_sub = current_user.password_hash.removeprefix("keycloak:")
    if keycloak_sub and keycloak_sub != current_user.password_hash:
        try:
            if kc.admin is not None:
                kc.admin.set_user_password(
                    keycloak_sub, body.new_password, temporary=False
                )
        except Exception:
            logger.exception(
                "Failed to update Keycloak password for user %s", current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password in identity provider",
            )

    # Record in password history
    await PasswordPolicyService.record_password_usage(db, current_user.id, new_hash)

    # Update password age
    from datetime import UTC, datetime

    from sqlalchemy import update

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(password_last_changed_at=datetime.now(UTC))
    )

    # Invalidate all sessions (except current)
    await invalidate_all_sessions(db, current_user.id)

    # Send notification
    await NotificationService.send_password_changed_notification(current_user.email)

    await db.commit()

    return PasswordChangeResponse(message="Password changed successfully")


@router.post("/admin/reset", response_model=PasswordChangeResponse)
async def admin_reset_password(
    body: PasswordResetConfirm,
    target_user_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    kc: KeycloakService = Depends(KeycloakService),
):
    """Admin-assisted password reset (requires Admin role)."""
    # Check admin role
    from app.models.role import Role
    from app.models.user_role import UserRole

    result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    user_roles = {row[0] for row in result.all()}

    if "Admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    import uuid as _uuid

    try:
        uid = _uuid.UUID(target_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )

    # Look up target user
    result = await db.execute(select(User).where(User.id == uid))
    target_user = result.scalar_one_or_none()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    # Validate new password policy
    is_valid, message = PasswordPolicyService.validate_password(body.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # Update password in Keycloak
    keycloak_sub = target_user.password_hash.removeprefix("keycloak:")
    if keycloak_sub and keycloak_sub != target_user.password_hash:
        try:
            if kc.admin is not None:
                kc.admin.set_user_password(
                    keycloak_sub, body.new_password, temporary=False
                )
        except Exception:
            logger.exception(
                "Failed to update Keycloak password for user %s", uid
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password in identity provider",
            )

    # Record in password history
    import bcrypt

    new_hash = bcrypt.hashpw(
        body.new_password.encode(), bcrypt.gensalt()
    ).decode()
    await PasswordPolicyService.record_password_usage(db, uid, new_hash)

    # Update password age
    from datetime import UTC, datetime

    from sqlalchemy import update

    await db.execute(
        update(User)
        .where(User.id == uid)
        .values(password_last_changed_at=datetime.now(UTC))
    )

    # Invalidate all sessions for target user
    await invalidate_all_sessions(db, uid)

    # Notify both admin and target user
    await NotificationService.send_admin_password_reset_notification(
        current_user.email, target_user.email
    )
    await NotificationService.send_password_changed_notification(target_user.email)

    await db.commit()

    return PasswordChangeResponse(
        message=f"Password reset successfully for {target_user.email}"
    )
