"""Integration tests for medical history (allergies, conditions, surgeries, family history)."""

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
    create_patient,
    create_role,
    create_user,
)

PREFIX = "/api/v1/patients"


# ── Helper ────────────────────────────────────────────────────────────────


async def _setup_user(db_session, admin_user):
    """Create a user with patient permissions and return auth header."""
    perm_create = await create_permission(db_session, "patient", "create")
    perm_read = await create_permission(db_session, "patient", "read")
    perm_update = await create_permission(db_session, "patient", "update")
    role = await create_role(db_session, name="MedHistoryUser")
    await assign_permission_to_role(db_session, role, perm_create)
    await assign_permission_to_role(db_session, role, perm_read)
    await assign_permission_to_role(db_session, role, perm_update)
    user = await create_user(
        db_session,
        email="medhistory@test.com",
        first_name="Med",
        last_name="User",
    )
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    token = create_access_token(sub=str(user.id), email=user.email)
    return auth_header(token), user.id


async def _create_test_patient(db_session, admin_user):
    """Create a patient and return (patient_id, headers, user_id)."""
    headers, user_id = await _setup_user(db_session, admin_user)
    patient = await create_patient(db_session, first_name="Test", last_name="Patient")
    await db_session.commit()
    return str(patient.id), headers, user_id


# ── Allergy Tests ─────────────────────────────────────────────────────────


async def test_create_allergy(client: AsyncClient, db_session, admin_user):
    """Create an allergy for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    payload = {
        "name": "Penicillin",
        "severity": "severe",
        "reaction": "Anaphylaxis",
        "status": "active",
        "source": "patient-reported",
        "icd10_code": "Z88.0",
    }
    resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/allergies",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["name"] == "Penicillin"
    assert data["severity"] == "severe"
    assert data["patient_id"] == patient_id


async def test_list_allergies(client: AsyncClient, db_session, admin_user):
    """List allergies for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    # Create two allergies
    for name in ["Penicillin", "Aspirin"]:
        await client.post(
            f"{PREFIX}/{patient_id}/medical-history/allergies",
            json={"name": name, "severity": "mild", "source": "clinical"},
            headers=headers,
        )
    resp = await client.get(
        f"{PREFIX}/{patient_id}/medical-history/allergies",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


async def test_update_allergy(client: AsyncClient, db_session, admin_user):
    """Update an allergy."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/allergies",
        json={"name": "Penicillin", "severity": "mild", "source": "patient-reported"},
        headers=headers,
    )
    allergy_id = create_resp.json()["id"]
    resp = await client.put(
        f"{PREFIX}/{patient_id}/medical-history/allergies/{allergy_id}",
        json={"severity": "severe", "reaction": "Hives"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["severity"] == "severe"
    assert resp.json()["reaction"] == "Hives"


async def test_delete_allergy(client: AsyncClient, db_session, admin_user):
    """Delete an allergy."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/allergies",
        json={"name": "Penicillin", "severity": "mild", "source": "patient-reported"},
        headers=headers,
    )
    allergy_id = create_resp.json()["id"]
    resp = await client.delete(
        f"{PREFIX}/{patient_id}/medical-history/allergies/{allergy_id}",
        headers=headers,
    )
    assert resp.status_code == 204


async def test_allergy_invalid_severity(client: AsyncClient, db_session, admin_user):
    """Invalid severity is rejected."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/allergies",
        json={"name": "Penicillin", "severity": "extreme", "source": "patient-reported"},
        headers=headers,
    )
    assert resp.status_code == 422


# ── Condition Tests ───────────────────────────────────────────────────────


async def test_create_condition(client: AsyncClient, db_session, admin_user):
    """Create a condition for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    payload = {
        "name": "Hypertension",
        "clinical_status": "active",
        "verification_status": "confirmed",
        "severity": "moderate",
        "onset_date": "2020-01-15",
        "source": "clinical",
    }
    resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/conditions",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["name"] == "Hypertension"
    assert data["clinical_status"] == "active"


async def test_list_conditions(client: AsyncClient, db_session, admin_user):
    """List conditions for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    for name in ["Hypertension", "Diabetes"]:
        await client.post(
            f"{PREFIX}/{patient_id}/medical-history/conditions",
            json={"name": name, "source": "clinical"},
            headers=headers,
        )
    resp = await client.get(
        f"{PREFIX}/{patient_id}/medical-history/conditions",
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_update_condition(client: AsyncClient, db_session, admin_user):
    """Update a condition."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/conditions",
        json={"name": "Hypertension", "source": "clinical"},
        headers=headers,
    )
    condition_id = create_resp.json()["id"]
    resp = await client.put(
        f"{PREFIX}/{patient_id}/medical-history/conditions/{condition_id}",
        json={"clinical_status": "remission", "notes": "Under control"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["clinical_status"] == "remission"


async def test_delete_condition(client: AsyncClient, db_session, admin_user):
    """Delete a condition."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/conditions",
        json={"name": "Hypertension", "source": "clinical"},
        headers=headers,
    )
    condition_id = create_resp.json()["id"]
    resp = await client.delete(
        f"{PREFIX}/{patient_id}/medical-history/conditions/{condition_id}",
        headers=headers,
    )
    assert resp.status_code == 204


# ── Surgery Tests ─────────────────────────────────────────────────────────


async def test_create_surgery(client: AsyncClient, db_session, admin_user):
    """Create a surgery for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    payload = {
        "name": "Appendectomy",
        "procedure_date": "2019-05-20",
        "surgeon": "Dr. Adeyemi",
        "facility": "Lagos University Teaching Hospital",
        "outcome": "Successful",
        "source": "patient-reported",
    }
    resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/surgeries",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["name"] == "Appendectomy"
    assert data["procedure_date"] == "2019-05-20"


async def test_list_surgeries(client: AsyncClient, db_session, admin_user):
    """List surgeries for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    for name in ["Appendectomy", "Knee Surgery"]:
        await client.post(
            f"{PREFIX}/{patient_id}/medical-history/surgeries",
            json={"name": name, "procedure_date": "2019-05-20", "source": "clinical"},
            headers=headers,
        )
    resp = await client.get(
        f"{PREFIX}/{patient_id}/medical-history/surgeries",
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_update_surgery(client: AsyncClient, db_session, admin_user):
    """Update a surgery."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/surgeries",
        json={"name": "Appendectomy", "procedure_date": "2019-05-20", "source": "clinical"},
        headers=headers,
    )
    surgery_id = create_resp.json()["id"]
    resp = await client.put(
        f"{PREFIX}/{patient_id}/medical-history/surgeries/{surgery_id}",
        json={"surgeon": "Dr. Adeyemi", "outcome": "Successful"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["surgeon"] == "Dr. Adeyemi"


async def test_delete_surgery(client: AsyncClient, db_session, admin_user):
    """Delete a surgery."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/surgeries",
        json={"name": "Appendectomy", "procedure_date": "2019-05-20", "source": "clinical"},
        headers=headers,
    )
    surgery_id = create_resp.json()["id"]
    resp = await client.delete(
        f"{PREFIX}/{patient_id}/medical-history/surgeries/{surgery_id}",
        headers=headers,
    )
    assert resp.status_code == 204


# ── Family History Tests ─────────────────────────────────────────────────


async def test_create_family_history(client: AsyncClient, db_session, admin_user):
    """Create family history for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    payload = {
        "condition_name": "Diabetes",
        "relationship_type": "Father",
        "onset_age": 50,
        "is_hereditary": True,
        "status": "living",
    }
    resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/family",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["condition_name"] == "Diabetes"
    assert data["relationship_type"] == "Father"


async def test_list_family_history(client: AsyncClient, db_session, admin_user):
    """List family history for a patient."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    for name in ["Diabetes", "Hypertension"]:
        await client.post(
            f"{PREFIX}/{patient_id}/medical-history/family",
            json={"condition_name": name, "relationship_type": "Father"},
            headers=headers,
        )
    resp = await client.get(
        f"{PREFIX}/{patient_id}/medical-history/family",
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_update_family_history(client: AsyncClient, db_session, admin_user):
    """Update family history."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/family",
        json={"condition_name": "Diabetes", "relationship_type": "Father"},
        headers=headers,
    )
    item_id = create_resp.json()["id"]
    resp = await client.put(
        f"{PREFIX}/{patient_id}/medical-history/family/{item_id}",
        json={"onset_age": 55, "is_hereditary": True},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["onset_age"] == 55


async def test_delete_family_history(client: AsyncClient, db_session, admin_user):
    """Delete family history."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/family",
        json={"condition_name": "Diabetes", "relationship_type": "Father"},
        headers=headers,
    )
    item_id = create_resp.json()["id"]
    resp = await client.delete(
        f"{PREFIX}/{patient_id}/medical-history/family/{item_id}",
        headers=headers,
    )
    assert resp.status_code == 204


# ── Auth Tests ────────────────────────────────────────────────────────────


async def test_medical_history_requires_auth(client: AsyncClient, db_session):
    """Unauthenticated requests are rejected."""
    patient_id = str(uuid.uuid4())
    resp = await client.get(f"{PREFIX}/{patient_id}/medical-history/allergies")
    assert resp.status_code == 401


async def test_medical_history_requires_permission(client: AsyncClient, db_session, admin_user):
    """Users without permission are rejected."""
    user = await create_user(
        db_session,
        email="noperm@test.com",
        first_name="No",
        last_name="Perm",
    )
    await db_session.commit()
    token = create_access_token(sub=str(user.id), email=user.email)
    headers = auth_header(token)
    patient_id = str(uuid.uuid4())
    resp = await client.get(
        f"{PREFIX}/{patient_id}/medical-history/allergies",
        headers=headers,
    )
    assert resp.status_code == 403


# ── Cross-Patient Isolation ──────────────────────────────────────────────


async def test_cannot_access_other_patient_allergies(client: AsyncClient, db_session, admin_user):
    """Users cannot access allergies of other patients via IDOR."""
    patient_id, headers, _ = await _create_test_patient(db_session, admin_user)
    other_patient = await create_patient(db_session, first_name="Other", last_name="Patient", mrn="LAG-000099")
    await db_session.commit()
    other_id = str(other_patient.id)

    # Create allergy for our patient
    create_resp = await client.post(
        f"{PREFIX}/{patient_id}/medical-history/allergies",
        json={"name": "Penicillin", "severity": "mild", "source": "patient-reported"},
        headers=headers,
    )
    allergy_id = create_resp.json()["id"]

    # Try to update with other patient ID
    resp = await client.put(
        f"{PREFIX}/{other_id}/medical-history/allergies/{allergy_id}",
        json={"severity": "severe"},
        headers=headers,
    )
    assert resp.status_code == 404