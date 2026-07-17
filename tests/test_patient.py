"""Integration tests for patient registration, CRUD, and MRN generation."""

from __future__ import annotations

import re
import uuid
from datetime import date

import pytest
from httpx import AsyncClient

from app.models.patient import EmergencyContact, NextOfKin, Patient
from app.services.mrn import MRNService
from tests.conftest import (
    assign_permission_to_role,
    assign_role_to_user,
    auth_header,
    create_access_token,
    create_permission,
    create_patient,
    create_role,
    create_user,
)

PREFIX = "/api/v1/patients"


# ── Helper ────────────────────────────────────────────────────────────────


async def _setup_patient_user(db_session, admin_user):
    """Create a user with full patient permissions and return auth header."""
    perm_create = await create_permission(db_session, "patient", "create")
    perm_read = await create_permission(db_session, "patient", "read")
    perm_update = await create_permission(db_session, "patient", "update")
    role = await create_role(db_session, name="FrontDesk")
    await assign_permission_to_role(db_session, role, perm_create)
    await assign_permission_to_role(db_session, role, perm_read)
    await assign_permission_to_role(db_session, role, perm_update)
    user = await create_user(
        db_session,
        email="frontdesk@test.com",
        first_name="Front",
        last_name="Desk",
    )
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    token = create_access_token(sub=str(user.id), email=user.email)
    return auth_header(token)


# ── Valid patient payload ─────────────────────────────────────────────────

def _patient_payload(**overrides) -> dict:
    base = {
        "first_name": "Adebayo",
        "last_name": "Ogundimu",
        "date_of_birth": "1985-06-15",
        "gender": "Male",
        "phone": "08012345678",
        "email": "adebayo@example.com",
        "blood_group": "O+",
        "address_street": "15 Allen Avenue",
        "address_city": "Ikeja",
        "address_state": "Lagos",
        "emergency_contacts": [
            {"name": "Funke Ogundimu", "phone": "08098765432", "relationship": "Wife"},
        ],
        "next_of_kin": {
            "name": "Tunde Ogundimu",
            "phone": "07012345678",
            "relationship": "Brother",
            "address": "12 Surulere Lane, Lagos",
        },
    }
    base.update(overrides)
    return base


# ── POST /patients/ — registration ───────────────────────────────────────


async def test_register_patient(client: AsyncClient, db_session, admin_user):
    """Registering a patient returns 201 with MRN and demographics."""
    headers = await _setup_patient_user(db_session, admin_user)
    resp = await client.post(
        PREFIX + "/",
        json=_patient_payload(),
        headers=headers,
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert re.match(r"^LAG-\d{6}$", data["mrn"])
    assert data["first_name"] == "Adebayo"
    assert data["last_name"] == "Ogundimu"
    assert data["status"] == "active"
    assert data["gender"] == "Male"
    assert data["phone"] == "08012345678"


async def test_register_patient_generates_unique_mrn(
    client: AsyncClient, db_session, admin_user
):
    """Three registrations produce three distinct MRNs."""
    headers = await _setup_patient_user(db_session, admin_user)
    mrns = set()
    for i in range(3):
        resp = await client.post(
            PREFIX + "/",
            json=_patient_payload(
                first_name=f"Patient{i}",
                phone=f"0801234567{i}",
                email=f"p{i}@example.com",
                emergency_contacts=[
                    {"name": f"Contact{i}", "phone": f"0809876543{i}", "relationship": "Parent"},
                ],
                next_of_kin={
                    "name": f"NOK{i}",
                    "phone": f"0701234567{i}",
                    "relationship": "Sibling",
                },
            ),
            headers=headers,
        )
        assert resp.status_code == 201
        mrns.add(resp.json()["mrn"])
    assert len(mrns) == 3


async def test_register_patient_with_emergency_contacts(
    client: AsyncClient, db_session, admin_user
):
    """Registration with 2 emergency contacts stores both."""
    headers = await _setup_patient_user(db_session, admin_user)
    payload = _patient_payload(
        emergency_contacts=[
            {"name": "Contact One", "phone": "08011111111", "relationship": "Wife"},
            {"name": "Contact Two", "phone": "08022222222", "relationship": "Father"},
        ],
    )
    resp = await client.post(PREFIX + "/", json=payload, headers=headers)
    assert resp.status_code == 201
    patient_id = resp.json()["id"]

    # Verify emergency contacts via direct DB query
    from sqlalchemy import select
    result = await db_session.execute(
        select(EmergencyContact).where(EmergencyContact.patient_id == uuid.UUID(patient_id))
    )
    contacts = list(result.scalars().all())
    assert len(contacts) == 2
    names = {c.name for c in contacts}
    assert names == {"Contact One", "Contact Two"}


async def test_register_patient_with_next_of_kin(
    client: AsyncClient, db_session, admin_user
):
    """Registration stores next of kin."""
    headers = await _setup_patient_user(db_session, admin_user)
    payload = _patient_payload()
    resp = await client.post(PREFIX + "/", json=payload, headers=headers)
    assert resp.status_code == 201
    patient_id = resp.json()["id"]

    from sqlalchemy import select
    result = await db_session.execute(
        select(NextOfKin).where(NextOfKin.patient_id == uuid.UUID(patient_id))
    )
    nok = result.scalar_one()
    assert nok.name == "Tunde Ogundimu"
    assert nok.relationship == "Brother"


async def test_register_patient_duplicate_warning(
    client: AsyncClient, db_session, admin_user
):
    """Second registration with same name + DOB returns 409."""
    headers = await _setup_patient_user(db_session, admin_user)
    payload = _patient_payload()
    resp1 = await client.post(PREFIX + "/", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = await client.post(PREFIX + "/", json=payload, headers=headers)
    assert resp2.status_code == 409
    assert "duplicate" in resp2.json()["detail"].lower()


# ── Phone validation ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "phone",
    [
        "08012345678",
        "09012345678",
        "07012345678",
        "+2348012345678",
        "+2349012345678",
    ],
)
async def test_nigerian_phone_valid(
    client: AsyncClient, db_session, admin_user, phone
):
    """Valid Nigerian phone numbers are accepted."""
    headers = await _setup_patient_user(db_session, admin_user)
    payload = _patient_payload(phone=phone)
    resp = await client.post(PREFIX + "/", json=payload, headers=headers)
    assert resp.status_code == 201


@pytest.mark.parametrize(
    "phone",
    [
        "12345",
        "+1234567890",
        "0801234567",
        "080123456789",
        "abcdefghijk",
    ],
)
async def test_nigerian_phone_invalid(
    client: AsyncClient, db_session, admin_user, phone
):
    """Invalid phone numbers are rejected with 422."""
    headers = await _setup_patient_user(db_session, admin_user)
    payload = _patient_payload(phone=phone)
    resp = await client.post(PREFIX + "/", json=payload, headers=headers)
    assert resp.status_code == 422


# ── GET /patients/ ───────────────────────────────────────────────────────


async def test_get_patient(client: AsyncClient, db_session, admin_user):
    """Register then GET returns matching patient."""
    headers = await _setup_patient_user(db_session, admin_user)
    reg = await client.post(PREFIX + "/", json=_patient_payload(), headers=headers)
    patient_id = reg.json()["id"]

    resp = await client.get(f"{PREFIX}/{patient_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == patient_id
    assert resp.json()["first_name"] == "Adebayo"


async def test_get_patient_not_found(client: AsyncClient, db_session, admin_user):
    """GET nonexistent UUID returns 404."""
    headers = await _setup_patient_user(db_session, admin_user)
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"{PREFIX}/{fake_id}", headers=headers)
    assert resp.status_code == 404


# ── GET /patients/ (list) ────────────────────────────────────────────────


async def test_list_patients(client: AsyncClient, db_session, admin_user):
    """List returns registered patients."""
    headers = await _setup_patient_user(db_session, admin_user)
    for i in range(3):
        await client.post(
            PREFIX + "/",
            json=_patient_payload(
                first_name=f"List{i}",
                phone=f"0801234567{i}",
                email=f"list{i}@example.com",
                emergency_contacts=[
                    {"name": f"LC{i}", "phone": f"0809876543{i}", "relationship": "Parent"},
                ],
                next_of_kin={
                    "name": f"LN{i}",
                    "phone": f"0701234567{i}",
                    "relationship": "Sibling",
                },
            ),
            headers=headers,
        )
    resp = await client.get(PREFIX + "/", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# ── PUT /patients/{id} ───────────────────────────────────────────────────


async def test_update_patient(client: AsyncClient, db_session, admin_user):
    """PUT updates patient phone and returns new value."""
    headers = await _setup_patient_user(db_session, admin_user)
    reg = await client.post(PREFIX + "/", json=_patient_payload(), headers=headers)
    patient_id = reg.json()["id"]

    resp = await client.put(
        f"{PREFIX}/{patient_id}",
        json={"phone": "08099999999"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["phone"] == "08099999999"


async def test_update_patient_not_found(client: AsyncClient, db_session, admin_user):
    """PUT nonexistent patient returns 404."""
    headers = await _setup_patient_user(db_session, admin_user)
    resp = await client.put(
        f"{PREFIX}/{uuid.uuid4()}",
        json={"phone": "08099999999"},
        headers=headers,
    )
    assert resp.status_code == 404


# ── MRN validation ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "mrn,valid",
    [
        ("LAG-000001", True),
        ("AB-123456", True),
        ("ABCDE-999999", True),
        ("lag-000001", False),
        ("L-000001", False),
        ("LAG-12345", False),
        ("LAG-1234567", False),
        ("LAG-00000A", False),
    ],
)
def test_mrn_format_validation(mrn: str, valid: bool):
    """MRNService.validate_mrn_format enforces PREFIX-NNNNNN."""
    assert MRNService.validate_mrn_format(mrn) is valid


async def test_mrn_generation(db_session):
    """MRNService.generate_mrn produces sequential MRNs."""
    mrn1 = await MRNService.generate_mrn(db_session, "TST")
    mrn2 = await MRNService.generate_mrn(db_session, "TST")
    assert mrn1 == "TST-000001"
    assert mrn2 == "TST-000002"
    assert MRNService.validate_mrn_format(mrn1)
    assert MRNService.validate_mrn_format(mrn2)


# ── Auth required ─────────────────────────────────────────────────────────


async def test_register_requires_auth(client: AsyncClient):
    """POST /patients/ without auth returns 401."""
    resp = await client.post(PREFIX + "/", json=_patient_payload())
    assert resp.status_code in (401, 403)


async def test_register_requires_permission(client: AsyncClient, db_session):
    """POST /patients/ with a user lacking patient:create returns 403."""
    user = await create_user(
        db_session, email="noperm@test.com", first_name="No", last_name="Perm"
    )
    await db_session.commit()
    token = create_access_token(sub=str(user.id), email=user.email)
    resp = await client.post(
        PREFIX + "/", json=_patient_payload(), headers=auth_header(token)
    )
    assert resp.status_code == 403
