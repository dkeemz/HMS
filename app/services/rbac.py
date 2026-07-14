from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.permission import Permission
from app.models.permission_override import PermissionOverride
from app.models.role import Role
from app.models.role_approval import RoleAssignmentApproval
from app.models.role_permission import RolePermission
from app.models.temporary_role import TemporaryRoleElevation
from app.models.user_role import UserRole

logger = logging.getLogger(__name__)

# Roles whose assignment requires department-head approval
_APPROVAL_REQUIRED_ROLES = {"Doctor", "Nurse", "Lab Tech", "Radiologist"}


class RBACService:
    """Central RBAC service for permission checks, role management, and auditing."""

    # ── Permission checking ──────────────────────────────────────────────

    @staticmethod
    async def check_permission(
        db: AsyncSession,
        user_id: uuid.UUID,
        resource: str,
        action: str,
    ) -> bool:
        """Check if user has (resource, action) via roles OR explicit overrides."""
        # 1. Check role-based permissions (only approved, non-expired roles)
        now = datetime.now(UTC)
        role_result = await db.execute(
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.status == "approved",
                )
            )
        )
        role_ids = [row[0] for row in role_result.all()]

        # Filter out expired temporary roles
        if role_ids:
            temp_result = await db.execute(
                select(TemporaryRoleElevation.role_id).where(
                    and_(
                        TemporaryRoleElevation.user_id == user_id,
                        TemporaryRoleElevation.role_id.in_(role_ids),
                        TemporaryRoleElevation.expires_at < now,
                    )
                )
            )
            expired_role_ids = {row[0] for row in temp_result.all()}
            role_ids = [rid for rid in role_ids if rid not in expired_role_ids]

        if role_ids:
            perm_result = await db.execute(
                select(Permission.resource, Permission.action)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id.in_(role_ids))
            )
            role_perms = {(row[0], row[1]) for row in perm_result.all()}
            if (resource, action) in role_perms:
                return True

        # 2. Check explicit permission overrides
        override_result = await db.execute(
            select(PermissionOverride.granted)
            .join(Permission, Permission.id == PermissionOverride.permission_id)
            .where(
                and_(
                    PermissionOverride.user_id == user_id,
                    Permission.resource == resource,
                    Permission.action == action,
                )
            )
            .order_by(PermissionOverride.created_at.desc())
            .limit(1)
        )
        override = override_result.scalar_one_or_none()
        if override is True:
            return True

        return False

    # ── Role assignment ──────────────────────────────────────────────────

    @staticmethod
    async def assign_role(
        db: AsyncSession,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        assigned_by: uuid.UUID,
    ) -> UserRole:
        """Assign a role to a user.

        For clinical roles (Doctor, Nurse, etc.) the assignment enters
        ``pending_approval`` status and a ``RoleAssignmentApproval`` row is
        created.  Other roles are assigned immediately.
        """
        # Look up the role name to decide if approval is required
        role = await db.get(Role, role_id)
        if role is None:
            raise ValueError("Role not found")

        requires_approval = role.name in _APPROVAL_REQUIRED_ROLES

        # Check for existing assignment
        existing = await db.execute(
            select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            )
        )
        existing_ur = existing.scalar_one_or_none()
        if existing_ur is not None:
            if existing_ur.status == "revoked":
                new_status = (
                    "pending_approval" if requires_approval else "approved"
                )
                existing_ur.status = new_status
                existing_ur.assigned_by = assigned_by
                existing_ur.assigned_at = datetime.now(UTC)
                ur = existing_ur
            else:
                raise ValueError("User already has this role")
        else:
            status = "pending_approval" if requires_approval else "approved"
            ur = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
                status=status,
            )
            db.add(ur)
            await db.flush()

        # Create approval record if needed
        if requires_approval and existing_ur is None:
            approval = RoleAssignmentApproval(
                user_role_id=ur.id,
                status="pending",
                requested_by=assigned_by,
            )
            db.add(approval)

        # Audit log
        await RBACService._audit_log(
            db,
            user_id=assigned_by,
            action="role_assigned",
            resource="role",
            resource_id=str(role_id),
            extra_data={
                "target_user_id": str(user_id),
                "role_name": role.name,
                "status": ur.status,
            },
        )

        await db.flush()
        logger.info(
            "Role '%s' assigned to user %s (status=%s)",
            role.name,
            user_id,
            ur.status,
        )

        await RBACService._notify_permission_change(
            db,
            user_id,
            "role_assigned",
            {"role_id": str(role_id), "role_name": role.name, "status": ur.status},
        )

        return ur

    @staticmethod
    async def approve_role_assignment(
        db: AsyncSession,
        approval_id: uuid.UUID,
        approved_by: uuid.UUID,
        decision: str = "approved",
    ) -> RoleAssignmentApproval:
        """Approve or reject a pending role assignment."""
        approval = await db.get(RoleAssignmentApproval, approval_id)
        if approval is None:
            raise ValueError("Approval record not found")
        if approval.status != "pending":
            raise ValueError("Approval already resolved")

        approval.status = decision
        approval.approved_by = approved_by
        approval.resolved_at = datetime.now(UTC)

        # Update the UserRole status
        ur = await db.get(UserRole, approval.user_role_id)
        if ur is not None:
            ur.status = decision

        await RBACService._audit_log(
            db,
            user_id=approved_by,
            action=f"role_{decision}",
            resource="role",
            resource_id=str(ur.role_id if ur else ""),
            extra_data={
                "approval_id": str(approval_id),
                "target_user_id": str(ur.user_id if ur else ""),
            },
        )

        await db.flush()
        return approval

    @staticmethod
    async def remove_role_from_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        removed_by: uuid.UUID,
    ) -> None:
        """Revoke a role assignment from a user."""
        result = await db.execute(
            select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            )
        )
        ur = result.scalar_one_or_none()
        if ur is None:
            raise ValueError("User does not have this role")

        ur.status = "revoked"

        await RBACService._audit_log(
            db,
            user_id=removed_by,
            action="role_revoked",
            resource="role",
            resource_id=str(role_id),
            extra_data={
                "target_user_id": str(user_id),
            },
        )

        await db.flush()

        await RBACService._notify_permission_change(
            db,
            user_id,
            "role_revoked",
            {"role_id": str(role_id)},
        )

    # ── Custom role creation ─────────────────────────────────────────────

    @staticmethod
    async def create_custom_role(
        db: AsyncSession,
        name: str,
        description: str,
        permission_ids: list[uuid.UUID],
        created_by: uuid.UUID,
    ) -> Role:
        """Create a custom role with specific permissions.

        Custom roles are non-system roles that require admin + dept head
        approval before becoming active.  The role is created with
        ``status="pending_approval"`` and a ``RoleAssignmentApproval``
        record is created to track the approval process.
        """
        existing = await db.execute(select(Role).where(Role.name == name))
        if existing.scalar_one_or_none() is not None:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(
            name=name, description=description, is_system=False,
            status="pending_approval",
        )
        db.add(role)
        await db.flush()

        for pid in permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=pid))

        approval = RoleAssignmentApproval(
            role_id=role.id,
            status="pending",
            requested_by=created_by,
        )
        db.add(approval)

        await RBACService._audit_log(
            db,
            user_id=created_by,
            action="role_created",
            resource="role",
            resource_id=str(role.id),
            extra_data={
                "role_name": name,
                "permission_count": len(permission_ids),
                "status": "pending_approval",
            },
        )

        await db.flush()
        logger.info(
            "Custom role '%s' created by user %s (pending approval)",
            name, created_by,
        )

        await RBACService._notify_permission_change(
            db,
            created_by,
            "role_created",
            {"role_id": str(role.id), "role_name": name, "status": "pending_approval"},
        )

        return role

    @staticmethod
    async def approve_custom_role(
        db: AsyncSession,
        approval_id: uuid.UUID,
        approved_by: uuid.UUID,
        decision: str = "approved",
        approver_role: str = "",
    ) -> RoleAssignmentApproval:
        """Approve or reject a custom role creation.

        Requires both admin and department-head approval.  The role only
        becomes active once both have approved.
        """
        approval = await db.get(RoleAssignmentApproval, approval_id)
        if approval is None:
            raise ValueError("Approval record not found")
        if approval.status not in ("pending", "partial"):
            raise ValueError("Approval already resolved")
        if approval.role_id is None:
            raise ValueError("This approval is not for a custom role")

        is_admin = approver_role in ("Admin", "System Administrator")
        is_dept_head = approver_role == "Department Head"

        if is_admin:
            approval.admin_approved = decision == "approved"
        elif is_dept_head:
            approval.dept_head_approved = decision == "approved"
        else:
            raise ValueError("Only Admin or Department Head can approve custom roles")

        if decision == "rejected":
            approval.status = "rejected"
            approval.approved_by = approved_by
            approval.resolved_at = datetime.now(UTC)
            role = await db.get(Role, approval.role_id)
            if role is not None:
                role.status = "rejected"
        elif approval.admin_approved and approval.dept_head_approved:
            approval.status = "approved"
            approval.approved_by = approved_by
            approval.resolved_at = datetime.now(UTC)
            role = await db.get(Role, approval.role_id)
            if role is not None:
                role.status = "active"
        else:
            approval.status = "partial"
            approval.approved_by = approved_by

        await RBACService._audit_log(
            db,
            user_id=approved_by,
            action=f"custom_role_{decision}",
            resource="role",
            resource_id=str(approval.role_id),
            extra_data={
                "approval_id": str(approval_id),
                "admin_approved": approval.admin_approved,
                "dept_head_approved": approval.dept_head_approved,
            },
        )

        await db.flush()
        return approval

    @staticmethod
    async def assign_permission_to_role(
        db: AsyncSession,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
        assigned_by: uuid.UUID,
    ) -> RolePermission:
        """Assign a permission to a role."""
        existing = await db.execute(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Permission already assigned to role")

        rp = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(rp)

        await RBACService._audit_log(
            db,
            user_id=assigned_by,
            action="permission_assigned_to_role",
            resource="role",
            resource_id=str(role_id),
            extra_data={"permission_id": str(permission_id)},
        )

        await db.flush()
        return rp

    @staticmethod
    async def remove_permission_from_role(
        db: AsyncSession,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
        removed_by: uuid.UUID,
    ) -> None:
        """Remove a permission from a role."""
        result = await db.execute(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                )
            )
        )
        rp = result.scalar_one_or_none()
        if rp is None:
            raise ValueError("Permission not assigned to role")

        await db.delete(rp)

        await RBACService._audit_log(
            db,
            user_id=removed_by,
            action="permission_removed_from_role",
            resource="role",
            resource_id=str(role_id),
            extra_data={"permission_id": str(permission_id)},
        )

        await db.flush()

    # ── Permission overrides ─────────────────────────────────────────────

    @staticmethod
    async def grant_permission_override(
        db: AsyncSession,
        user_id: uuid.UUID,
        permission_id: uuid.UUID,
        granted_by: uuid.UUID,
    ) -> PermissionOverride:
        """Grant an individual permission override to a user."""
        # Remove any existing override for this user/permission
        existing = await db.execute(
            select(PermissionOverride).where(
                and_(
                    PermissionOverride.user_id == user_id,
                    PermissionOverride.permission_id == permission_id,
                )
            )
        )
        for old in existing.scalars().all():
            await db.delete(old)

        override = PermissionOverride(
            user_id=user_id,
            permission_id=permission_id,
            granted=True,
            granted_by=granted_by,
        )
        db.add(override)

        await RBACService._audit_log(
            db,
            user_id=granted_by,
            action="permission_override_granted",
            resource="permission",
            resource_id=str(permission_id),
            extra_data={
                "target_user_id": str(user_id),
            },
        )

        await db.flush()
        return override

    @staticmethod
    async def revoke_permission_override(
        db: AsyncSession,
        user_id: uuid.UUID,
        permission_id: uuid.UUID,
        revoked_by: uuid.UUID,
    ) -> None:
        """Revoke an individual permission override from a user."""
        result = await db.execute(
            select(PermissionOverride).where(
                and_(
                    PermissionOverride.user_id == user_id,
                    PermissionOverride.permission_id == permission_id,
                )
            )
        )
        override = result.scalar_one_or_none()
        if override is None:
            raise ValueError("No permission override found")

        await db.delete(override)

        await RBACService._audit_log(
            db,
            user_id=revoked_by,
            action="permission_override_revoked",
            resource="permission",
            resource_id=str(permission_id),
            extra_data={
                "target_user_id": str(user_id),
            },
        )

        await db.flush()

    # ── Temporary role elevation ─────────────────────────────────────────

    @staticmethod
    async def temporary_role_elevation(
        db: AsyncSession,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        duration_hours: int,
        elevated_by: uuid.UUID,
    ) -> TemporaryRoleElevation:
        """Temporarily elevate a user's role with time-limited access."""
        if duration_hours < 1 or duration_hours > 72:
            raise ValueError("Duration must be between 1 and 72 hours")

        expires_at = datetime.now(UTC) + timedelta(hours=duration_hours)

        # Create or reactivate the UserRole
        existing = await db.execute(
            select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            )
        )
        ur = existing.scalar_one_or_none()
        if ur is not None:
            ur.status = "approved"
            ur.assigned_by = elevated_by
            ur.expires_at = expires_at
        else:
            ur = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=elevated_by,
                status="approved",
                expires_at=expires_at,
            )
            db.add(ur)
        await db.flush()

        # Create the tracking record
        elevation = TemporaryRoleElevation(
            user_id=user_id,
            role_id=role_id,
            expires_at=expires_at,
            elevated_by=elevated_by,
        )
        db.add(elevation)

        role = await db.get(Role, role_id)
        await RBACService._audit_log(
            db,
            user_id=elevated_by,
            action="temporary_role_elevation",
            resource="role",
            resource_id=str(role_id),
            extra_data={
                "target_user_id": str(user_id),
                "duration_hours": duration_hours,
                "expires_at": expires_at.isoformat(),
                "role_name": role.name if role else "",
            },
        )

        await db.flush()
        return elevation

    @staticmethod
    async def revoke_temporary_elevation(
        db: AsyncSession,
        elevation_id: uuid.UUID,
        revoked_by: uuid.UUID,
    ) -> None:
        """Revoke an active temporary elevation early."""
        elevation = await db.get(TemporaryRoleElevation, elevation_id)
        if elevation is None:
            raise ValueError("Elevation record not found")

        # Revoke the UserRole
        result = await db.execute(
            select(UserRole).where(
                and_(
                    UserRole.user_id == elevation.user_id,
                    UserRole.role_id == elevation.role_id,
                    UserRole.status == "approved",
                )
            )
        )
        ur = result.scalar_one_or_none()
        if ur is not None:
            ur.status = "revoked"
            ur.expires_at = None

        await db.delete(elevation)

        await RBACService._audit_log(
            db,
            user_id=revoked_by,
            action="temporary_role_revoked",
            resource="role",
            resource_id=str(elevation.role_id),
            extra_data={
                "target_user_id": str(elevation.user_id),
                "elevation_id": str(elevation_id),
            },
        )

        await db.flush()

    @staticmethod
    async def cleanup_expired_elevations(db: AsyncSession) -> int:
        """Remove expired temporary elevations. Returns count removed."""
        now = datetime.now(UTC)
        result = await db.execute(
            select(TemporaryRoleElevation).where(
                TemporaryRoleElevation.expires_at < now
            )
        )
        expired = result.scalars().all()

        for elev in expired:
            ur_result = await db.execute(
                select(UserRole).where(
                    and_(
                        UserRole.user_id == elev.user_id,
                        UserRole.role_id == elev.role_id,
                        UserRole.status == "approved",
                    )
                )
            )
            ur = ur_result.scalar_one_or_none()
            if ur is not None:
                ur.status = "revoked"
                ur.expires_at = None

            await db.delete(elev)

        if expired:
            await db.flush()
            logger.info("Cleaned up %d expired temporary elevations", len(expired))

        return len(expired)

    # ── Department-scoped access ─────────────────────────────────────────

    @staticmethod
    async def get_department_scope(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Get the department ID for department-scoped access.

        Returns the user's ``department_id`` if set, otherwise ``None``.
        """
        from app.models.user import User

        user = await db.get(User, user_id)
        if user is None:
            return None
        return user.department_id

    # ── Effective permissions ────────────────────────────────────────────

    @staticmethod
    async def get_user_permissions(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[dict[str, str]]:
        """Return all effective permissions for a user (roles + overrides)."""
        # Role-based permissions
        role_result = await db.execute(
            select(Permission.resource, Permission.action, Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.status == "approved",
                )
            )
            .distinct()
        )
        perms: dict[tuple[str, str], uuid.UUID] = {}
        source: dict[tuple[str, str], str] = {}

        for resource, action, pid in role_result.all():
            perms[(resource, action)] = pid
            source[(resource, action)] = "role"

        # Override permissions (take precedence)
        override_result = await db.execute(
            select(
                Permission.resource,
                Permission.action,
                Permission.id,
                PermissionOverride.granted,
            )
            .join(Permission, Permission.id == PermissionOverride.permission_id)
            .where(PermissionOverride.user_id == user_id)
            .order_by(PermissionOverride.created_at.desc())
        )

        seen: set[tuple[str, str]] = set()
        for resource, action, pid, granted in override_result.all():
            key = (resource, action)
            if key in seen:
                continue
            seen.add(key)
            if granted:
                perms[key] = pid
                source[key] = "override"
            else:
                perms.pop(key, None)
                source[key] = "override_revoke"

        return [
            {
                "resource": res,
                "action": act,
                "permission_id": str(perms[(res, act)]),
                "source": source[(res, act)],
            }
            for res, act in perms
        ]

    # ── Audit log ────────────────────────────────────────────────────────

    @staticmethod
    async def get_rbac_audit_log(
        db: AsyncSession,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query RBAC-related audit log entries."""
        stmt = select(AuditLog).where(
            AuditLog.resource.in_(["role", "permission", "user_role"])
        )
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ── Notifications ────────────────────────────────────────────────────

    @staticmethod
    async def _notify_permission_change(
        db: AsyncSession,
        target_user_id: uuid.UUID,
        action: str,
        details: dict,
    ) -> None:
        """Send notification for permission/role changes.

        Notifies the affected user and, for sensitive changes, the compliance
        officer via NotificationService (email delivery).
        """
        from app.models.user import User
        from app.services.notifications import NotificationService

        target = await db.get(User, target_user_id)
        if target:
            logger.info(
                "RBAC NOTIFICATION → %s | action=%s details=%s",
                target.email,
                action,
                details,
            )
            role_actions = {
                "role_assigned", "role_revoked", "role_created",
                "custom_role_approved", "custom_role_rejected",
            }
            if action in role_actions:
                await NotificationService.send_role_change_notification(
                    target.email, action, details,
                )
            elif action == "temporary_role_elevation":
                await NotificationService.send_temporary_elevation_notification(
                    target.email,
                    details.get("role_name", ""),
                    details.get("duration_hours", 0),
                    details.get("expires_at", ""),
                )
            else:
                await NotificationService.send_permission_change_notification(
                    target.email, action, details,
                )

        sensitive_actions = {
            "role_assigned",
            "role_revoked",
            "role_created",
            "permission_override_granted",
            "permission_override_revoked",
            "temporary_role_elevation",
        }
        if action in sensitive_actions:
            co_result = await db.execute(
                select(User.email)
                .join(UserRole, UserRole.user_id == User.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.name == "Compliance Officer")
                .distinct()
            )
            for (co_email,) in co_result.all():
                logger.info(
                    "COMPLIANCE NOTIFICATION → %s | action=%s target=%s",
                    co_email,
                    action,
                    target.email if target else target_user_id,
                )
                await NotificationService.send_compliance_notification(
                    co_email, action, details,
                )

    # ── Internal helpers ─────────────────────────────────────────────────

    @staticmethod
    async def _audit_log(
        db: AsyncSession,
        user_id: uuid.UUID,
        action: str,
        resource: str,
        resource_id: str = "",
        extra_data: dict | None = None,
    ) -> AuditLog:
        """Create a tamper-evident audit log entry."""
        # Compute hash from previous entry
        prev_result = await db.execute(
            select(AuditLog.hash)
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        prev_hash = prev_result.scalar_one_or_none() or ""

        payload = json.dumps(
            {
                "user_id": str(user_id),
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "extra_data": extra_data,
                "prev_hash": prev_hash,
            },
            sort_keys=True,
        )
        entry_hash = hashlib.sha256(payload.encode()).hexdigest()

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            extra_data=extra_data,
            previous_hash=prev_hash,
            hash=entry_hash,
        )
        db.add(log_entry)
        return log_entry
