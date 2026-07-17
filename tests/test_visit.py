"""Integration tests for visit history tracking (Plan 02-06)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from httpx import AsyncClient

from tests.conftest import (
    assign_permission_to_role,
    assign_role_to_user,
    auth_header,
    create_access_token,
    create_permission,
    create_role,
    create_user,
)


async def _setup_user_with_patient_perms(db_session):
    """Create a user with full patient permissions and return auth header."""
    perm_create = await create_permission(db_session, "patient", "create")
    perm_read = await create_permission(db_session, "patient", "read")
    perm_update = await create_permission(db_session, "patient", "update")
    perm_delete = await create_permission(db_session, "patient", "delete")
    role = await create_role(db_session, name="VisitStaff")
    await assign_permission_to_role(db_session, role, perm_create)
    await assign_permission_to_role(db_session, role, perm_read)
    await assign_permission_to_role(db_session, role, perm_update)
    await assign_permission_to_role(db_session, role, perm_delete)
    user = await create_user(
        db_session,
        email="visitstaff@test.com",
        first_name="Visit",
        last_name="Staff",
    )
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    token = create_access_token(sub=str(user.id), email=user.email)
    return auth_header(token)


async def _create_patient(client, headers):
    resp = await client.post(
        "/api/v1/patients/",
        json={
            "first_name": "Visit",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "phone": "08012345001",
            "email": "visit.patient@test.com",
            "blood_group": "O+",
            "address_street": "123 Test St",
            "address_city": "Lagos",
            "address_state": "Lagos",
            "emergency_contacts": [
                {"name": "Emergency Contact", "phone": "08098765001", "relationship": "Wife"},
            ],
            "next_of_kin": {
                "name": "Next of Kin",
                "phone": "07012345001",
                "relationship": "Brother",
                "address": "12 Surulere Lane, Lagos",
            },
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_walkin_visit(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/walkin",
        json={
            "reason": "consultation",
            "reason_notes": "Chest pain",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "checked-in"
    assert data["checked_in_at"] is not None
    assert data["reason"] == "consultation"


@pytest.mark.asyncio
async def test_create_scheduled_visit(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits",
        json={
            "reason": "follow-up",
            "scheduled_at": "2026-08-01T10:00:00Z",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "scheduled"
    assert data["scheduled_at"] is not None


@pytest.mark.asyncio
async def test_transition_checked_in_to_in_progress(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    visit_resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/walkin",
        json={"reason": "procedure"},
        headers=headers,
    )
    visit_id = visit_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/transition",
        json={"new_status": "in-progress"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in-progress"
    assert resp.json()["started_at"] is not None


@pytest.mark.asyncio
async def test_transition_in_progress_to_completed(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    visit_resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/walkin",
        json={"reason": "consultation"},
        headers=headers,
    )
    visit_id = visit_resp.json()["id"]

    await client.post(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/transition",
        json={"new_status": "in-progress"},
        headers=headers,
    )

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/transition",
        json={"new_status": "completed"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None
    assert data["duration_minutes"] is not None


@pytest.mark.asyncio
async def test_invalid_transition_scheduled_to_completed(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    visit_resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits",
        json={
            "reason": "lab",
            "scheduled_at": "2026-09-01T14:00:00Z",
        },
        headers=headers,
    )
    visit_id = visit_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/transition",
        json={"new_status": "completed"},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_cancel_visit(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    visit_resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/walkin",
        json={"reason": "other"},
        headers=headers,
    )
    visit_id = visit_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/transition",
        json={"new_status": "cancelled", "reason": "Patient no-show"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    assert data["cancelled_at"] is not None
    assert data["cancellation_reason"] == "Patient no-show"


@pytest.mark.asyncio
async def test_get_visits_for_patient(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    for reason in ["consultation", "follow-up", "lab"]:
        await client.post(
            f"/api/v1/patients/{patient_id}/visits/walkin",
            json={"reason": reason},
            headers=headers,
        )

    resp = await client.get(
        f"/api/v1/patients/{patient_id}/visits",
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_get_visit_summary(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    visit_resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/walkin",
        json={"reason": "consultation"},
        headers=headers,
    )
    visit_id = visit_resp.json()["id"]

    await client.post(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/transition",
        json={"new_status": "in-progress"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/transition",
        json={"new_status": "completed"},
        headers=headers,
    )

    resp = await client.get(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/summary",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["visit_id"] == visit_id
    assert "Visit reason" in data["notes"]


@pytest.mark.asyncio
async def test_get_visit_summary_not_found(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    visit_resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/walkin",
        json={"reason": "vaccination"},
        headers=headers,
    )
    visit_id = visit_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/patients/{patient_id}/visits/{visit_id}/summary",
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_reason(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    resp = await client.post(
        f"/api/v1/patients/{patient_id}/visits/walkin",
        json={"reason": "invalid_reason"},
        headers=headers,
    )
    # Pydantic Literal validation catches invalid reason (422)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_visit_not_found(client: AsyncClient, db_session):
    headers = await _setup_user_with_patient_perms(db_session)
    patient_id = await _create_patient(client, headers)

    resp = await client.get(
        f"/api/v1/patients/{patient_id}/visits/{uuid.uuid4()}",
        headers=headers,
    )
    assert resp.status_code == 404
