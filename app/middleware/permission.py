from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status
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
