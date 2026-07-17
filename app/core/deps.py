from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_keycloak_token, get_current_user
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole

logger = logging.getLogger(__name__)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user has an active account."""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_user_from_cookie(
    access_token: str | None = Cookie(None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate from the ``access_token`` cookie (for HTML page routes).

    Raises RedirectResponse to /auth/login if the cookie is missing or invalid.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login"},
        )
    try:
        payload = decode_keycloak_token(access_token)
    except Exception:
        logger.warning("Cookie token validation failed")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login"},
        )

    try:
        user = await sync_user_from_cookie(db, payload)
    except Exception:
        logger.warning("User sync from cookie failed")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login"},
        )
    return user


async def sync_user_from_cookie(db: AsyncSession, payload: dict) -> User:
    """Look up the HMS user from a decoded JWT payload."""
    from app.core.security import sync_user_from_keycloak
    return await sync_user_from_keycloak(db, payload)


def require_role(role_name: str):
    """Dependency factory that enforces a specific role assignment.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role("Admin"))])
        async def admin_view():
            ...
    """

    async def _role_checker(
        current_user: CurrentUser,
        db: AsyncSession = Depends(get_db),
    ) -> User:
        result = await db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == current_user.id)
        )
        user_roles = {row[0] for row in result.all()}

        if role_name not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required",
            )
        return current_user

    return _role_checker


def require_any_role(*role_names: str):
    """Require the user to hold at least one of the listed roles."""

    async def _checker(
        current_user: CurrentUser,
        db: AsyncSession = Depends(get_db),
    ) -> User:
        result = await db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == current_user.id)
        )
        user_roles = {row[0] for row in result.all()}

        if not user_roles.intersection(role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {role_names} required",
            )
        return current_user

    return _checker
