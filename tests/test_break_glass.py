"""Integration tests for break-glass emergency access endpoints."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.conftest import auth_header, create_access_token

PREFIX = "/api/v1/break-glass"


# ── POST /break-glass/request ────────────────────────────────────────────


async def test_doctor_can_request_break_glass(
    client: AsyncClient, doctor_user, db_session
):
    """Doctor can request break-glass access."""
    patient_id = uuid.uuid4()
    token = create_access_token(sub=str(doctor_user.id), email=doctor_user.email)
    resp = await client.post(
        f"{PREFIX}/request",
        json={
            "patient_id": str(patient_id),
            "reason": "Emergency chest pain — need immediate access to records",
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["doctor_id"] == str(doctor_user.id)
    assert data["patient_id"] == str(patient_id)


async def test_non_doctor_cannot_request_break_glass(
    client: AsyncClient, admin_user
):
    """Non-doctor gets 403 when requesting break-glass."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/request",
        json={
            "patient_id": str(uuid.uuid4()),
            "reason": "Emergency test — need immediate access to records",
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 403


# ── POST /break-glass/{id}/approve ───────────────────────────────────────


async def test_admin_can_approve_break_glass(
    client: AsyncClient, admin_user, doctor_user, db_session
):
    """Admin can approve a pending break-glass request."""
    from app.models.break_glass import BreakGlassAccess

    patient_id = uuid.uuid4()
    bg = BreakGlassAccess(
        doctor_id=doctor_user.id,
        patient_id=patient_id,
        reason="Emergency test — need immediate access to records",
        status="pending",
    )
    db_session.add(bg)
    await db_session.flush()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/{bg.id}/approve",
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == str(admin_user.id)


async def test_admin_can_deny_break_glass(
    client: AsyncClient, admin_user, doctor_user, db_session
):
    """Admin can deny a pending break-glass request."""
    from app.models.break_glass import BreakGlassAccess

    bg = BreakGlassAccess(
        doctor_id=doctor_user.id,
        patient_id=uuid.uuid4(),
        reason="Emergency test — need immediate access to records",
        status="pending",
    )
    db_session.add(bg)
    await db_session.flush()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/{bg.id}/deny",
        json={"reason": "Insufficient justification for access"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "denied"


# ── GET /break-glass/pending ─────────────────────────────────────────────


async def test_get_pending_requests(client: AsyncClient, admin_user, db_session):
    """Admin can list pending break-glass requests."""
    from app.models.break_glass import BreakGlassAccess

    bg = BreakGlassAccess(
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        reason="Emergency test — pending review for records",
        status="pending",
    )
    db_session.add(bg)
    await db_session.flush()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/pending", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_non_admin_cannot_list_pending(
    client: AsyncClient, doctor_user
):
    """Non-admin gets 403 on pending requests."""
    token = create_access_token(sub=str(doctor_user.id), email=doctor_user.email)
    resp = await client.get(f"{PREFIX}/pending", headers=auth_header(token))
    assert resp.status_code == 403


# ── GET /break-glass/check/{patient_id} ──────────────────────────────────


async def test_check_access_returns_false(
    client: AsyncClient, doctor_user
):
    """Doctor with no access gets has_access=False."""
    token = create_access_token(sub=str(doctor_user.id), email=doctor_user.email)
    resp = await client.get(
        f"{PREFIX}/check/{uuid.uuid4()}",
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_access"] is False


# ── GET /break-glass/history ─────────────────────────────────────────────


async def test_get_break_glass_history_as_admin(
    client: AsyncClient, admin_user, db_session
):
    """Admin can view break-glass history."""
    from app.models.break_glass import BreakGlassAccess

    bg = BreakGlassAccess(
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        reason="Historical entry — need access to records for audit",
        status="approved",
    )
    db_session.add(bg)
    await db_session.flush()

    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/history", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
