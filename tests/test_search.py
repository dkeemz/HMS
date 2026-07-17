from __future__ import annotations

import asyncio
import time
import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.patient import Patient
from tests.conftest import (
    auth_header,
    create_access_token,
    create_patient,
    create_permission,
    create_role,
    assign_permission_to_role,
    assign_role_to_user,
    create_user,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture()
async def search_user(db_session: AsyncSession):
    """Create a user with patient:read permission for search tests."""
    user = await create_user(db_session, email="searcher@hms.local")
    role = await create_role(db_session, name="SearchRole")
    perm = await create_permission(db_session, resource="patient", action="read")
    await assign_permission_to_role(db_session, role, perm)
    await assign_role_to_user(db_session, user, role)
    await db_session.commit()
    token = create_access_token(sub=str(user.id), email="searcher@hms.local")
    return user, token


@pytest.fixture()
async def search_patients(db_session: AsyncSession):
    """Create a set of patients for search tests."""
    patients = []
    specs = [
        ("John", "Smith", "LAG-000001", "08012345678", "Male", "active"),
        ("Jane", "Doe", "LAG-000002", "08012345679", "Female", "active"),
        ("Johnny", "Walker", "LAG-000003", "08098765432", "Male", "active"),
        ("Janet", "Jackson", "LAG-000004", "08011112222", "Female", "inactive"),
        ("Bob", "Johnson", "LAG-000005", "08033334444", "Male", "active"),
    ]
    for fn, ln, mrn, phone, gender, status in specs:
        p = await create_patient(
            db_session,
            first_name=fn, last_name=ln, mrn=mrn,
            phone=phone, gender=gender, status=status,
        )
        patients.append(p)
    await db_session.commit()
    return patients


# ── Tests ─────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_search_by_name(client: AsyncClient, search_user, search_patients):
    """Search by first name finds matching patients."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "john"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2  # John Smith and Bob Johnson
    names = [r["first_name"] + " " + r["last_name"] for r in data["results"]]
    assert any("John Smith" in n for n in names)
    assert any("Bob Johnson" in n for n in names)


@pytest.mark.anyio
async def test_search_by_mrn(client: AsyncClient, search_user, search_patients):
    """Search by MRN finds the exact patient."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "LAG-000"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    mrns = [r["mrn"] for r in data["results"]]
    assert "LAG-000001" in mrns


@pytest.mark.anyio
async def test_search_by_phone(client: AsyncClient, search_user, search_patients):
    """Search by phone number finds matching patients."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "0801234"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    phones = [r["phone"] for r in data["results"]]
    assert "08012345678" in phones


@pytest.mark.anyio
async def test_search_minimum_length(client: AsyncClient, search_user):
    """Search with less than 4 chars returns 422 validation error (D-19)."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "ab"},
        headers=auth_header(token),
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_search_pagination(client: AsyncClient, search_user, db_session: AsyncSession):
    """Pagination returns correct page and total (D-20)."""
    _, token = search_user
    # Create 60 patients to test pagination
    for i in range(60):
        await create_patient(
            db_session,
            first_name=f"Patient{i}",
            last_name=f"Search{i:03d}",
            mrn=f"PAG-{i:06d}",
            phone=f"0801{str(i).zfill(7)}",
        )
    await db_session.commit()

    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "Search", "page": 1, "page_size": 50},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 60
    assert len(data["results"]) == 50
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert data["total_pages"] >= 2

    # Page 2
    resp2 = await client.get(
        "/api/v1/patients/search",
        params={"q": "Search", "page": 2, "page_size": 50},
        headers=auth_header(token),
    )
    assert resp2.status_code == 200
    assert len(resp2.json()["results"]) >= 10


@pytest.mark.anyio
async def test_search_with_status_filter(client: AsyncClient, search_user, search_patients):
    """Status filter returns only matching patients."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "a", "status": "inactive"},  # using 4+ chars
        headers=auth_header(token),
    )
    # "a" is too short — need 4 chars
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "Janet", "status": "inactive"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for r in data["results"]:
        assert r["status"] == "inactive"


@pytest.mark.anyio
async def test_search_with_gender_filter(client: AsyncClient, search_user, search_patients):
    """Gender filter returns only matching patients."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "Jane", "gender": "Female"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    for r in data["results"]:
        assert r["gender"] == "Female"


@pytest.mark.anyio
async def test_search_audit_log(client: AsyncClient, search_user, search_patients, db_session):
    """Every search produces an audit log entry (D-68)."""
    user, token = search_user
    await client.get(
        "/api/v1/patients/search",
        params={"q": "Smith"},
        headers=auth_header(token),
    )
    from sqlalchemy import select
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.user_id == user.id,
            AuditLog.action == "patient_search",
        )
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.extra_data is not None
    assert log.extra_data["query"] == "Smith"
    assert log.extra_data["results_count"] >= 1


@pytest.mark.anyio
async def test_search_no_results(client: AsyncClient, search_user, search_patients):
    """Search for nonexistent term returns 0 results."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "ZZZZZNONEXISTENT"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert len(data["results"]) == 0


@pytest.mark.anyio
async def test_typeahead(client: AsyncClient, search_user, search_patients):
    """Typeahead returns top 10 with minimal fields."""
    _, token = search_user
    resp = await client.get(
        "/api/v1/patients/search/typeahead",
        params={"q": "John"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 10
    for item in data:
        assert "id" in item
        assert "mrn" in item
        assert "first_name" in item
        assert "last_name" in item
        assert "status" in item
        # Typeahead should NOT return full patient details
        assert "date_of_birth" not in item
        assert "phone" not in item


@pytest.mark.anyio
async def test_search_performance(client: AsyncClient, search_user, db_session: AsyncSession):
    """Search returns within 2 seconds even with 1000 patients."""
    _, token = search_user
    # Create 1000 patients
    for i in range(1000):
        await create_patient(
            db_session,
            first_name=f"Bulk{i}",
            last_name=f"Patient{i:04d}",
            mrn=f"BULK-{i:06d}",
            phone=f"0801{str(i).zfill(7)}"[:11],
        )
    await db_session.commit()

    start = time.monotonic()
    resp = await client.get(
        "/api/v1/patients/search",
        params={"q": "Bulk500"},
        headers=auth_header(token),
    )
    elapsed = time.monotonic() - start
    assert resp.status_code == 200
    assert elapsed < 2.0, f"Search took {elapsed:.2f}s, expected < 2s"
