from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.permission import Permission
from app.models.role import Role
from app.schemas.rbac import (
    ApprovalDecision,
    ApprovalResponse,
    AuditLogEntry,
    AuditLogResponse,
    EffectivePermission,
    EffectivePermissionsResponse,
    PermissionMatrixResponse,
    PermissionMatrixRole,
    PermissionOverrideRequest,
    PermissionOverrideResponse,
    PermissionResponse,
    RoleCreate,
    RoleListResponse,
    RoleResponse,
    TemporaryElevationRequest,
    TemporaryElevationResponse,
    UserRoleAssign,
    UserRoleResponse,
)
from app.services.rbac import RBACService

router = APIRouter(prefix="/rbac", tags=["rbac"])


# ── Role endpoints ───────────────────────────────────────────────────────


@router.get("/roles", response_model=RoleListResponse)
async def list_roles(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all roles with permission counts."""
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
    )
    roles = result.scalars().all()

    return RoleListResponse(
        roles=[
            RoleResponse(
                id=str(r.id),
                name=r.name,
                description=r.description,
                is_system=r.is_system,
                permission_count=len(r.permissions),
                created_at=r.created_at,
            )
            for r in roles
        ]
    )


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    body: RoleCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Create a custom role with specific permissions."""
    # Verify permission IDs exist
    if body.permission_ids:
        perm_result = await db.execute(
            select(Permission.id).where(Permission.id.in_(body.permission_ids))
        )
        found_ids = {row[0] for row in perm_result.all()}
        missing = set(body.permission_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission IDs not found: {missing}",
            )

    try:
        role = await RBACService.create_custom_role(
            db,
            name=body.name,
            description=body.description or "",
            permission_ids=body.permission_ids,
            created_by=current_user.id,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return RoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permission_count=len(body.permission_ids),
        created_at=role.created_at,
    )


@router.post(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_201_CREATED,
)
async def assign_permission_to_role(
    role_id: uuid.UUID,
    body: PermissionOverrideRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Assign a permission to a role."""
    try:
        await RBACService.assign_permission_to_role(
            db,
            role_id=role_id,
            permission_id=body.permission_id,
            assigned_by=current_user.id,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return {"message": "Permission assigned to role"}


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_permission_from_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Remove a permission from a role."""
    try:
        await RBACService.remove_permission_from_role(
            db,
            role_id=role_id,
            permission_id=permission_id,
            removed_by=current_user.id,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── User role assignment ─────────────────────────────────────────────────


@router.post(
    "/users/{user_id}/roles",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_role_to_user(
    user_id: uuid.UUID,
    body: UserRoleAssign,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Assign a role to a user (may require dept head approval)."""
    try:
        ur = await RBACService.assign_role(
            db,
            user_id=user_id,
            role_id=body.role_id,
            assigned_by=current_user.id,
        )
        # Fetch role name
        role = await db.get(Role, ur.role_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return UserRoleResponse(
        id=str(ur.id),
        user_id=str(ur.user_id),
        role_id=str(ur.role_id),
        role_name=role.name if role else "",
        status=ur.status,
        assigned_by=str(ur.assigned_by) if ur.assigned_by else None,
        assigned_at=ur.assigned_at,
        expires_at=ur.expires_at,
    )


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_role_from_user(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Remove a role from a user."""
    try:
        await RBACService.remove_role_from_user(
            db,
            user_id=user_id,
            role_id=role_id,
            removed_by=current_user.id,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/users/{user_id}/permissions",
    response_model=EffectivePermissionsResponse,
)
async def get_user_permissions(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get all effective permissions for a user."""
    permissions = await RBACService.get_user_permissions(db, user_id)
    return EffectivePermissionsResponse(
        user_id=str(user_id),
        permissions=[
            EffectivePermission(
                resource=p["resource"],
                action=p["action"],
                permission_id=p["permission_id"],
                source=p["source"],
            )
            for p in permissions
        ],
    )


# ── Permission overrides ─────────────────────────────────────────────────


@router.post(
    "/users/{user_id}/permissions/override",
    response_model=PermissionOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_permission_override(
    user_id: uuid.UUID,
    body: PermissionOverrideRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Grant an individual permission override to a user."""
    try:
        override = await RBACService.grant_permission_override(
            db,
            user_id=user_id,
            permission_id=body.permission_id,
            granted_by=current_user.id,
        )
        await RBACService._notify_permission_change(
            db, user_id, "permission_override_granted",
            {"permission_id": str(body.permission_id)},
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return PermissionOverrideResponse(
        id=str(override.id),
        user_id=str(override.user_id),
        permission_id=str(override.permission_id),
        granted=override.granted,
        granted_by=str(override.granted_by),
        created_at=override.created_at,
    )


@router.delete(
    "/users/{user_id}/permissions/override/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_permission_override(
    user_id: uuid.UUID,
    permission_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Revoke an individual permission override from a user."""
    try:
        await RBACService.revoke_permission_override(
            db,
            user_id=user_id,
            permission_id=permission_id,
            revoked_by=current_user.id,
        )
        await RBACService._notify_permission_change(
            db, user_id, "permission_override_revoked",
            {"permission_id": str(permission_id)},
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── Temporary role elevation ─────────────────────────────────────────────


@router.post(
    "/users/{user_id}/elevate",
    response_model=TemporaryElevationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def temporary_role_elevation(
    user_id: uuid.UUID,
    body: TemporaryElevationRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Temporarily elevate a user's role."""
    try:
        elevation = await RBACService.temporary_role_elevation(
            db,
            user_id=user_id,
            role_id=body.role_id,
            duration_hours=body.duration_hours,
            elevated_by=current_user.id,
        )
        await RBACService._notify_permission_change(
            db, user_id, "temporary_role_elevation",
            {
                "role_id": str(body.role_id),
                "duration_hours": body.duration_hours,
            },
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return TemporaryElevationResponse(
        id=str(elevation.id),
        user_id=str(elevation.user_id),
        role_id=str(elevation.role_id),
        expires_at=elevation.expires_at,
        elevated_by=str(elevation.elevated_by),
        created_at=elevation.created_at,
    )


@router.delete(
    "/elevations/{elevation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_temporary_elevation(
    elevation_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Revoke an active temporary elevation early."""
    try:
        await RBACService.revoke_temporary_elevation(
            db,
            elevation_id=elevation_id,
            revoked_by=current_user.id,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── Approvals ────────────────────────────────────────────────────────────


@router.get("/approvals", response_model=list[ApprovalResponse])
async def list_pending_approvals(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List pending role assignment approvals."""
    from app.models.role_approval import RoleAssignmentApproval

    result = await db.execute(
        select(RoleAssignmentApproval)
        .where(RoleAssignmentApproval.status == "pending")
        .order_by(RoleAssignmentApproval.created_at.desc())
    )
    approvals = result.scalars().all()

    return [
        ApprovalResponse(
            id=str(a.id),
            user_role_id=str(a.user_role_id),
            status=a.status,
            requested_by=str(a.requested_by),
            approved_by=str(a.approved_by) if a.approved_by else None,
            created_at=a.created_at,
            resolved_at=a.resolved_at,
        )
        for a in approvals
    ]


@router.post(
    "/approvals/{approval_id}",
    response_model=ApprovalResponse,
)
async def resolve_approval(
    approval_id: uuid.UUID,
    body: ApprovalDecision,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a pending role assignment."""
    try:
        approval = await RBACService.approve_role_assignment(
            db,
            approval_id=approval_id,
            approved_by=current_user.id,
            decision=body.decision,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ApprovalResponse(
        id=str(approval.id),
        user_role_id=str(approval.user_role_id),
        status=approval.status,
        requested_by=str(approval.requested_by),
        approved_by=str(approval.approved_by) if approval.approved_by else None,
        created_at=approval.created_at,
        resolved_at=approval.resolved_at,
    )


# ── Permission matrix ────────────────────────────────────────────────────


@router.get("/matrix", response_model=PermissionMatrixResponse)
async def get_permission_matrix(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get the full permission matrix (all roles × all permissions)."""
    perm_result = await db.execute(
        select(Permission).order_by(Permission.resource, Permission.action)
    )
    permissions = perm_result.scalars().all()

    role_result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
    )
    roles = role_result.scalars().all()

    return PermissionMatrixResponse(
        permissions=[
            PermissionResponse(
                id=str(p.id),
                resource=p.resource,
                action=p.action,
                description=p.description,
            )
            for p in permissions
        ],
        roles=[
            PermissionMatrixRole(
                role_id=str(r.id),
                role_name=r.name,
                permission_ids=[
                    str(rp.permission_id) for rp in r.permissions
                ],
            )
            for r in roles
        ],
    )


# ── Audit log ────────────────────────────────────────────────────────────


@router.get("/audit", response_model=AuditLogResponse)
async def get_rbac_audit_log(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get audit log for role/permission changes."""
    entries = await RBACService.get_rbac_audit_log(
        db,
        user_id=user_id,
        action=action,
        limit=limit,
        offset=offset,
    )
    return AuditLogResponse(
        entries=[
            AuditLogEntry(
                id=str(e.id),
                user_id=str(e.user_id) if e.user_id else None,
                action=e.action,
                resource=e.resource,
                resource_id=e.resource_id,
                extra_data=e.extra_data,
                timestamp=e.timestamp,
            )
            for e in entries
        ]
    )
