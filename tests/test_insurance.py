"""Tests for Insurance Management (Plan 02-04)."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.models.insurance_policy import InsurancePolicy
from app.models.patient import InsuranceProvider, Patient
from tests.conftest import (
    assign_permission_to_role,
    assign_role_to_user,
    auth_header,
    create_access_token,
    create_patient,
    create_permission,
    create_role,
    create_user,
)


@pytest.fixture()
async def insurance_provider(db_session) -> InsuranceProvider:
    provider = InsuranceProvider(
        name="Test HMO",
        provider_type="HMO",
        short_code="TST",
        website="https://test.com",
    )
    db_session.add(provider)
    await db_session.flush()
    return provider


@pytest.fixture()
async def patient_with_user(db_session) -> tuple[Patient, dict]:
    """Create a patient and return patient + auth headers."""
    user = await create_user(db_session, email="receptionist@hms.local")
    role = await create_role(db_session, name="Receptionist")
    perm_read = await create_permission(db_session, resource="patient", action="read")
    perm_update = await create_permission(db_session, resource="patient", action="update")
    await assign_permission_to_role(db_session, role, perm_read)
    await assign_permission_to_role(db_session, role, perm_update)
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()

    patient = await create_patient(db_session, mrn="LAG-INS-001")
    await db_session.commit()

    token = create_access_token(sub=str(user.id), email=user.email)
    return patient, auth_header(token)


class TestInsurancePolicyCRUD:
    @pytest.mark.asyncio
    async def test_create_insurance_policy(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-001",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["policy_number"] == "POL-001"
        assert data["status"] == "pending"
        assert data["policy_type"] == "primary"
        assert isinstance(data["id"], str)  # UUID serialized as string

    @pytest.mark.asyncio
    async def test_create_multiple_policies(
        self, client: AsyncClient, patient_with_user, insurance_provider, db_session
    ):
        patient, headers = patient_with_user
        provider2 = InsuranceProvider(
            name="Second HMO", provider_type="HMO", short_code="SEC"
        )
        db_session.add(provider2)
        await db_session.flush()

        for ptype in ["primary", "secondary"]:
            pid = str(insurance_provider.id) if ptype == "primary" else str(provider2.id)
            resp = await client.post(
                f"/api/v1/patients/{patient.id}/insurance",
                headers=headers,
                json={
                    "provider_id": pid,
                    "policy_number": f"POL-{ptype.upper()}",
                    "policy_type": ptype,
                    "coverage_type": "HMO",
                    "start_date": date.today().isoformat(),
                },
            )
            assert resp.status_code == 201

        resp = await client.get(
            f"/api/v1/patients/{patient.id}/insurance", headers=headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_list_policies(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-LIST",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        resp = await client.get(
            f"/api/v1/patients/{patient.id}/insurance", headers=headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_single_policy(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        create_resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-GET",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        policy_id = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["policy_number"] == "POL-GET"

    @pytest.mark.asyncio
    async def test_get_policy_not_found(
        self, client: AsyncClient, patient_with_user
    ):
        patient, headers = patient_with_user
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/v1/patients/{patient.id}/insurance/{fake_id}", headers=headers
        )
        assert resp.status_code == 404


class TestInsuranceStateTransitions:
    @pytest.mark.asyncio
    async def test_transition_pending_to_verified(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        create_resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-VER",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        policy_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "verified"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "verified"
        assert resp.json()["verified_at"] is not None

    @pytest.mark.asyncio
    async def test_transition_verified_to_active(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        create_resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-ACT",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        policy_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "verified"},
        )
        resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "active"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"
        assert resp.json()["activated_at"] is not None

    @pytest.mark.asyncio
    async def test_transition_active_to_expired(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        create_resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-EXP",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        policy_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "verified"},
        )
        await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "active"},
        )
        resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "expired"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "expired"
        assert resp.json()["expired_at"] is not None

    @pytest.mark.asyncio
    async def test_invalid_transition_pending_to_active(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        create_resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-INV",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        policy_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "active"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_expired_terminal_state(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        create_resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-TERM",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        policy_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "verified"},
        )
        await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "active"},
        )
        await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "expired"},
        )
        resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance/{policy_id}/transition",
            headers=headers,
            json={"new_status": "verified"},
        )
        assert resp.status_code == 409


class TestInsuranceProviders:
    @pytest.mark.asyncio
    async def test_get_providers(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        _, headers = patient_with_user
        resp = await client.get(
            "/api/v1/insurance/providers",
            headers=headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["short_code"] == "TST"


class TestExpiredPolicyWarning:
    @pytest.mark.asyncio
    async def test_expired_policy_warning(
        self, client: AsyncClient, patient_with_user, insurance_provider
    ):
        patient, headers = patient_with_user
        create_resp = await client.post(
            f"/api/v1/patients/{patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(insurance_provider.id),
                "policy_number": "POL-EXPIRED",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": (date.today() - timedelta(days=365)).isoformat(),
                "end_date": (date.today() - timedelta(days=1)).isoformat(),
            },
        )
        policy_id = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/patients/{patient.id}/insurance/expired", headers=headers
        )
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert policy_id in ids


class TestInsurancePermissions:
    @pytest.mark.asyncio
    async def test_insurance_no_permission(
        self, client: AsyncClient, db_session, sample_patient
    ):
        user = await create_user(db_session, email="noperm@hms.local")
        role = await create_role(db_session, name="NoPerm")
        perm = await create_permission(db_session, resource="patient", action="read")
        await assign_permission_to_role(db_session, role, perm)
        await assign_role_to_user(db_session, user, role)
        await db_session.commit()

        token = create_access_token(sub=str(user.id), email=user.email)
        headers = auth_header(token)

        resp = await client.post(
            f"/api/v1/patients/{sample_patient.id}/insurance",
            headers=headers,
            json={
                "provider_id": str(uuid.uuid4()),
                "policy_number": "POL-NO",
                "policy_type": "primary",
                "coverage_type": "HMO",
                "start_date": date.today().isoformat(),
            },
        )
        assert resp.status_code == 403
