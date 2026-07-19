"""Seed predefined roles and permission hierarchy for HMS.

Usage:
    python -m app.seeds.roles

Requires a running PostgreSQL instance and DATABASE_URL configured in .env.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


# ---------------------------------------------------------------------------
# Permission definitions — resource:action pairs
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PermSpec:
    resource: str
    action: str
    description: str


PERMISSION_SPECS: list[PermSpec] = [
    PermSpec("user", "create", "Create users"),
    PermSpec("user", "read", "View user profiles"),
    PermSpec("user", "update", "Edit user profiles"),
    PermSpec("user", "delete", "Deactivate / remove users"),
    PermSpec("role", "manage", "Create, edit, assign roles"),
    PermSpec("patient", "create", "Register new patients"),
    PermSpec("patient", "read", "View patient records"),
    PermSpec("patient", "update", "Edit patient records"),
    PermSpec("patient", "delete", "Archive / remove patient records"),
    PermSpec("appointment", "create", "Schedule appointments"),
    PermSpec("appointment", "read", "View appointments"),
    PermSpec("appointment", "update", "Reschedule / update appointments"),
    PermSpec("appointment", "delete", "Cancel appointments"),
    PermSpec("medical_record", "create", "Create medical records"),
    PermSpec("medical_record", "read", "View medical records"),
    PermSpec("medical_record", "update", "Update medical records"),
    PermSpec("medical_record", "delete", "Delete medical records"),
    PermSpec("prescription", "create", "Create prescriptions"),
    PermSpec("prescription", "read", "View prescriptions"),
    PermSpec("prescription", "update", "Update prescriptions"),
    PermSpec("prescription", "delete", "Void prescriptions"),
    PermSpec("lab_order", "create", "Order lab tests"),
    PermSpec("lab_order", "read", "View lab orders"),
    PermSpec("lab_order", "update", "Update lab orders"),
    PermSpec("lab_result", "create", "Record lab results"),
    PermSpec("lab_result", "read", "View lab results"),
    PermSpec("lab_result", "update", "Update lab results"),
    PermSpec("radiology_order", "create", "Order imaging studies"),
    PermSpec("radiology_order", "read", "View radiology orders"),
    PermSpec("radiology_result", "create", "Record radiology results"),
    PermSpec("radiology_result", "read", "View radiology results"),
    PermSpec("pharmacy", "create", "Dispense medications"),
    PermSpec("pharmacy", "read", "View medication inventory"),
    PermSpec("pharmacy", "update", "Update medication inventory"),
    PermSpec("billing", "create", "Create invoices"),
    PermSpec("billing", "read", "View billing records"),
    PermSpec("billing", "update", "Update invoices / payments"),
    PermSpec("billing", "delete", "Void invoices"),
    PermSpec("report", "read", "View reports and analytics"),
    PermSpec("report", "export", "Export reports"),
    PermSpec("audit_log", "read", "View audit logs"),
    PermSpec("system", "configure", "Configure system settings"),
    PermSpec("compliance", "read", "View compliance data"),
    PermSpec("compliance", "manage", "Manage compliance policies"),
    PermSpec("department", "create", "Create departments"),
    PermSpec("department", "read", "View departments"),
    PermSpec("department", "update", "Edit departments"),
    PermSpec("department", "delete", "Delete departments"),
    PermSpec("doctor", "read", "View doctor profiles"),
    PermSpec("doctor", "update", "Edit doctor profiles"),
    PermSpec("appointment", "create", "Create appointments"),
    PermSpec("appointment", "read", "View appointments"),
    PermSpec("appointment", "update", "Edit/update appointments"),
    PermSpec("appointment", "delete", "Cancel appointments"),
]


# ---------------------------------------------------------------------------
# Role definitions with their permission keys (resource:action)
# ---------------------------------------------------------------------------
ROLES: dict[str, dict] = {
    "Super Admin": {
        "description": "Full system access — inherits every permission",
        # is_system roles are marked True
        "permissions": "*ALL*",
    },
    "Admin": {
        "description": "Administrative access excluding system-level config",
        "permissions": [
            "user:create",
            "user:read",
            "user:update",
            "user:delete",
            "role:manage",
            "patient:create",
            "patient:read",
            "patient:update",
            "patient:delete",
            "appointment:create",
            "appointment:read",
            "appointment:update",
            "appointment:delete",
            "medical_record:create",
            "medical_record:read",
            "medical_record:update",
            "medical_record:delete",
            "prescription:create",
            "prescription:read",
            "prescription:update",
            "prescription:delete",
            "lab_order:create",
            "lab_order:read",
            "lab_order:update",
            "lab_result:create",
            "lab_result:read",
            "lab_result:update",
            "radiology_order:create",
            "radiology_order:read",
            "radiology_result:create",
            "radiology_result:read",
            "pharmacy:create",
            "pharmacy:read",
            "pharmacy:update",
            "billing:create",
            "billing:read",
            "billing:update",
            "billing:delete",
            "report:read",
            "report:export",
            "audit_log:read",
            "compliance:read",
            "compliance:manage",
            "department:create",
            "department:read",
            "department:update",
            "department:delete",
            "doctor:read",
            "doctor:update",
            "appointment:create",
            "appointment:read",
            "appointment:update",
            "appointment:delete",
        ],
    },
    "Dept Head": {
        "description": "Department head — manages department staff and records",
        "permissions": [
            "user:read",
            "user:update",
            "patient:create",
            "patient:read",
            "patient:update",
            "patient:delete",
            "appointment:create",
            "appointment:read",
            "appointment:update",
            "appointment:delete",
            "medical_record:create",
            "medical_record:read",
            "medical_record:update",
            "medical_record:delete",
            "prescription:create",
            "prescription:read",
            "prescription:update",
            "lab_order:create",
            "lab_order:read",
            "lab_order:update",
            "lab_result:create",
            "lab_result:read",
            "lab_result:update",
            "radiology_order:create",
            "radiology_order:read",
            "radiology_result:create",
            "radiology_result:read",
            "report:read",
            "report:export",
            "department:read",
            "doctor:read",
        ],
    },
    "Doctor": {
        "description": "Physician — clinical access to patient records",
        "permissions": [
            "patient:create",
            "patient:read",
            "patient:update",
            "appointment:create",
            "appointment:read",
            "appointment:update",
            "medical_record:create",
            "medical_record:read",
            "medical_record:update",
            "prescription:create",
            "prescription:read",
            "prescription:update",
            "lab_order:create",
            "lab_order:read",
            "lab_result:read",
            "radiology_order:create",
            "radiology_order:read",
            "radiology_result:read",
            "report:read",
            "department:read",
            "doctor:read",
        ],
    },
    "Nurse": {
        "description": "Nursing staff — patient care and vitals",
        "permissions": [
            "patient:create",
            "patient:read",
            "patient:update",
            "appointment:read",
            "appointment:update",
            "medical_record:create",
            "medical_record:read",
            "medical_record:update",
            "prescription:read",
            "lab_order:read",
            "lab_result:read",
            "report:read",
            "department:read",
            "doctor:read",
        ],
    },
    "Pharmacist": {
        "description": "Pharmacy operations — dispensing and inventory",
        "permissions": [
            "patient:read",
            "prescription:read",
            "prescription:update",
            "pharmacy:create",
            "pharmacy:read",
            "pharmacy:update",
            "report:read",
        ],
    },
    "Lab Tech": {
        "description": "Laboratory technician — test processing and results",
        "permissions": [
            "patient:read",
            "lab_order:read",
            "lab_result:create",
            "lab_result:read",
            "lab_result:update",
            "report:read",
        ],
    },
    "Radiologist": {
        "description": "Radiology specialist — imaging and diagnostics",
        "permissions": [
            "patient:read",
            "radiology_order:read",
            "radiology_result:create",
            "radiology_result:read",
            "medical_record:read",
            "report:read",
        ],
    },
    "Receptionist": {
        "description": "Front desk — scheduling and patient registration",
        "permissions": [
            "patient:create",
            "patient:read",
            "patient:update",
            "appointment:create",
            "appointment:read",
            "appointment:update",
            "appointment:delete",
            "billing:create",
            "billing:read",
        ],
    },
    "Billing": {
        "description": "Billing and financial operations",
        "permissions": [
            "patient:read",
            "billing:create",
            "billing:read",
            "billing:update",
            "billing:delete",
            "report:read",
            "report:export",
        ],
    },
    "Compliance Officer": {
        "description": "Regulatory compliance and policy management",
        "permissions": [
            "user:read",
            "patient:read",
            "audit_log:read",
            "compliance:read",
            "compliance:manage",
            "report:read",
            "report:export",
        ],
    },
    "System Auditor": {
        "description": "Read-only access for auditing and compliance reviews",
        "permissions": [
            "user:read",
            "patient:read",
            "medical_record:read",
            "audit_log:read",
            "compliance:read",
            "report:read",
            "report:export",
        ],
    },
    "Chief Medical Director": {
        "description": "Executive clinical leadership — full clinical visibility",
        "permissions": [
            "user:read",
            "user:update",
            "patient:create",
            "patient:read",
            "patient:update",
            "patient:delete",
            "appointment:create",
            "appointment:read",
            "appointment:update",
            "medical_record:create",
            "medical_record:read",
            "medical_record:update",
            "medical_record:delete",
            "prescription:create",
            "prescription:read",
            "lab_order:create",
            "lab_order:read",
            "lab_result:read",
            "radiology_order:read",
            "radiology_result:read",
            "report:read",
            "report:export",
            "compliance:read",
        ],
    },
    "Medical Director": {
        "description": "Medical director — clinical oversight and reporting",
        "permissions": [
            "user:read",
            "patient:read",
            "patient:update",
            "appointment:read",
            "medical_record:read",
            "medical_record:update",
            "prescription:read",
            "lab_order:read",
            "lab_result:read",
            "radiology_result:read",
            "report:read",
            "report:export",
        ],
    },
    "Minister of Health": {
        "description": "Government oversight — system-wide read access and reporting",
        "permissions": [
            "user:read",
            "patient:read",
            "medical_record:read",
            "audit_log:read",
            "compliance:read",
            "report:read",
            "report:export",
        ],
    },
}


def _perm_key(spec: PermSpec) -> str:
    return f"{spec.resource}:{spec.action}"


async def _get_or_create_permissions(
    session: AsyncSession,
) -> dict[str, Permission]:
    """Load or create all permission rows. Return a resource:action -> model map."""
    specs_map = {_perm_key(s): s for s in PERMISSION_SPECS}
    existing = (await session.execute(select(Permission))).scalars().all()
    perm_map: dict[str, Permission] = {
        f"{p.resource}:{p.action}": p for p in existing
    }

    for key, spec in specs_map.items():
        if key not in perm_map:
            perm = Permission(
                resource=spec.resource,
                action=spec.action,
                description=spec.description,
            )
            session.add(perm)
            perm_map[key] = perm

    await session.flush()
    return perm_map


async def _get_or_create_roles(
    session: AsyncSession,
) -> dict[str, Role]:
    """Load or create all role rows."""
    existing = (await session.execute(select(Role))).scalars().all()
    role_map: dict[str, Role] = {r.name: r for r in existing}

    for name, spec in ROLES.items():
        if name not in role_map:
            role = Role(
                name=name,
                description=spec["description"],
                is_system=True,
            )
            session.add(role)
            role_map[name] = role

    await session.flush()
    return role_map


async def _assign_permissions(
    session: AsyncSession,
    role_map: dict[str, Role],
    perm_map: dict[str, Permission],
) -> None:
    """Assign permissions to each role based on the hierarchy."""
    all_perm_keys = set(perm_map.keys())

    # Check which role-permission pairs already exist
    existing_rp = (
        await session.execute(select(RolePermission))
    ).scalars().all()
    existing_pairs = {(rp.role_id, rp.permission_id) for rp in existing_rp}

    for name, spec in ROLES.items():
        role = role_map[name]
        perm_keys = spec["permissions"]

        if perm_keys == "*ALL*":
            keys_to_assign = all_perm_keys
        else:
            keys_to_assign = set(perm_keys)

        for key in keys_to_assign:
            perm = perm_map[key]
            if (role.id, perm.id) not in existing_pairs:
                session.add(
                    RolePermission(role_id=role.id, permission_id=perm.id)
                )

    await session.flush()


async def seed() -> None:
    """Run the full seed: permissions -> roles -> role-permissions."""
    async with async_session() as session:
        async with session.begin():
            perm_map = await _get_or_create_permissions(session)
            role_map = await _get_or_create_roles(session)
            await _assign_permissions(session, role_map, perm_map)

    print(f"Seeded {len(perm_map)} permissions")
    print(f"Seeded {len(role_map)} roles")
    print("Role-permission assignments complete")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
