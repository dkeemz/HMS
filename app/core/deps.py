from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


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
