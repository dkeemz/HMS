"""Integration tests for RBAC endpoints."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.conftest import (
    assign_permission_to_role,
    assign_role_to_user,
    auth_header,
    create_access_token,
    create_permission,
    create_role,
)

PREFIX = "/api/v1/rbac"


# ── GET /rbac/roles ──────────────────────────────────────────────────────


async def test_list_roles(client: AsyncClient, admin_user):
    """GET /rbac/roles returns list of roles."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/roles", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "roles" in data
    assert isinstance(data["roles"], list)
    assert len(data["roles"]) >= 1


async def test_list_roles_no_auth(client: AsyncClient):
    """GET /rbac/roles without token returns 401."""
    resp = await client.get(f"{PREFIX}/roles")
    assert resp.status_code == 401


# ── POST /rbac/roles ─────────────────────────────────────────────────────


async def test_create_role(client: AsyncClient, admin_user, sample_permission):
    """POST /rbac/roles creates a new custom role."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/roles",
        json={
            "name": "Custom Nurse",
            "description": "A custom nursing role",
            "permission_ids": [str(sample_permission.id)],
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Custom Nurse"
    assert data["permission_count"] == 1


async def test_create_role_duplicate_name(client: AsyncClient, admin_user, db_session):
    """POST /rbac/roles with existing name returns 409."""
    await create_role(db_session, name="DupRole")
    await db_session.commit()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/roles",
        json={"name": "DupRole"},
        headers=auth_header(token),
    )
    assert resp.status_code == 409


# ── POST /rbac/users/{user_id}/roles ────────────────────────────────────


async def test_assign_role_to_user(
    client: AsyncClient, admin_user, nurse_user, db_session,
):
    """POST /rbac/users/{uid}/roles assigns a role."""
    role = await create_role(db_session, name="Pharmacist")
    await db_session.commit()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/users/{nurse_user.id}/roles",
        json={"role_id": str(role.id)},
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["role_name"] == "Pharmacist"
    assert data["status"] == "approved"


async def test_assign_nonexistent_role(client: AsyncClient, admin_user, nurse_user):
    """Assigning a nonexistent role returns 400."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/users/{nurse_user.id}/roles",
        json={"role_id": str(uuid.uuid4())},
        headers=auth_header(token),
    )
    assert resp.status_code == 400


# ── DELETE /rbac/users/{user_id}/roles/{role_id} ────────────────────────


async def test_remove_role_from_user(
    client: AsyncClient, admin_user, nurse_user, db_session,
):
    """DELETE /rbac/users/{uid}/roles/{rid} revokes a role."""
    role = await create_role(db_session, name="ToRevoke")
    await assign_role_to_user(db_session, nurse_user, role)
    await db_session.commit()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.delete(
        f"{PREFIX}/users/{nurse_user.id}/roles/{role.id}",
        headers=auth_header(token),
    )
    assert resp.status_code == 204


# ── GET /rbac/users/{user_id}/permissions ────────────────────────────────


async def test_get_user_permissions(
    client: AsyncClient, admin_user, nurse_user, db_session,
):
    """GET /rbac/users/{uid}/permissions returns effective permissions."""
    perm = await create_permission(db_session, resource="medication", action="dispense")
    role = await create_role(db_session, name="Pharmacist")
    await assign_permission_to_role(db_session, role, perm)
    await assign_role_to_user(db_session, nurse_user, role)
    await db_session.commit()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(
        f"{PREFIX}/users/{nurse_user.id}/permissions",
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["permissions"]) >= 1
    resources = {p["resource"] for p in data["permissions"]}
    assert "medication" in resources


# ── GET /rbac/matrix ─────────────────────────────────────────────────────


async def test_get_permission_matrix(client: AsyncClient, admin_user, db_session):
    """GET /rbac/matrix returns full permission matrix."""
    perm = await create_permission(db_session, resource="lab", action="order")
    role = await create_role(db_session, name="LabTech")
    await assign_permission_to_role(db_session, role, perm)
    await db_session.commit()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/matrix", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "permissions" in data
    assert "roles" in data
    assert len(data["permissions"]) >= 1


# ── GET /rbac/audit ──────────────────────────────────────────────────────


async def test_get_rbac_audit_log(client: AsyncClient, admin_user):
    """GET /rbac/audit returns audit log entries."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/audit", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data


# ── POST /rbac/roles/{role_id}/permissions ───────────────────────────────


async def test_assign_permission_to_role_endpoint(
    client: AsyncClient, admin_user, db_session
):
    """POST /rbac/roles/{rid}/permissions assigns a permission to a role."""
    role = await create_role(db_session, name="TestAssignPerm")
    perm = await create_permission(db_session, resource="vitals", action="read")
    await db_session.commit()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/roles/{role.id}/permissions",
        json={"permission_id": str(perm.id)},
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "Permission assigned to role"


async def test_assign_permission_already_assigned(
    client: AsyncClient, admin_user, db_session
):
    """Assigning already-assigned permission returns 400."""
    role = await create_role(db_session, name="AlreadyPerm")
    perm = await create_permission(db_session, resource="vitals", action="write")
    await assign_permission_to_role(db_session, role, perm)
    await db_session.commit()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/roles/{role.id}/permissions",
        json={"permission_id": str(perm.id)},
        headers=auth_header(token),
    )
    assert resp.status_code == 400
