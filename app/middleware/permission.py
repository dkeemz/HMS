from __future__ import annotations

import logging
import uuid

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.services.rbac import RBACService

logger = logging.getLogger(__name__)


def require_permission(resource: str, action: str):
    """Dependency factory that enforces a specific permission.

    Checks both role-based permissions and explicit overrides.

    Usage::

        @router.get(
            "/patients",
            dependencies=[Depends(require_permission("patient", "read"))],
        )
        async def list_patients():
            ...
    """

    async def _checker(
        current_user: CurrentUser,
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        has_perm = await RBACService.check_permission(
            db, current_user.id, resource, action
        )
        if not has_perm:
            logger.warning(
                "Permission denied: user=%s resource=%s action=%s",
                current_user.id,
                resource,
                action,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{resource}:{action}' required",
            )
        return current_user

    return _checker


def require_any_permission(*permissions: tuple[str, str]):
    """Require the user to hold at least one of the listed permissions."""

    async def _checker(
        current_user: CurrentUser,
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        for resource, action in permissions:
            if await RBACService.check_permission(
                db, current_user.id, resource, action
            ):
                return current_user

        perm_strs = [f"{r}:{a}" for r, a in permissions]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of permissions {perm_strs} required",
        )

    return _checker


def require_department_scope():
    """Dependency that enforces department-scoped access for doctors.

    Doctors can only access resources within their own department.
    Non-doctor users (admins, etc.) are not restricted.

    Usage::

        @router.get(
            "/patients",
            dependencies=[
                Depends(require_permission("patient", "read")),
                Depends(require_department_scope()),
            ],
        )
        async def list_patients():
            ...
    """

    async def _checker(
        current_user: CurrentUser,
        db: AsyncSession = Depends(get_db),
        department_id: uuid.UUID | None = Query(None),
    ) -> CurrentUser:
        from app.models.role import Role
        from app.models.user_role import UserRole

        is_doctor = await db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                (UserRole.user_id == current_user.id)
                & (UserRole.status == "approved")
                & (Role.name == "Doctor")
            )
            .limit(1)
        )
        if is_doctor.scalar_one_or_none() is None:
            return current_user

        user_dept = await RBACService.get_department_scope(db, current_user.id)
        if user_dept is None:
            return current_user

        if department_id is not None and department_id != user_dept:
            logger.warning(
                "Department scope violation: user=%s user_dept=%s requested_dept=%s",
                current_user.id,
                user_dept,
                department_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted to your department",
            )

        return current_user

    return _checker
