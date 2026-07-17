# Phase 2: Patient Management - Pattern Map

**Mapped:** 2026-07-15
**Files analyzed:** 46 (new + modified)
**Analogs found:** 42 / 46

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/models/patient.py` | model | CRUD | `app/models/user.py` | exact |
| `app/models/mrn_sequence.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/emergency_contact.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/next_of_kin.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/allergy.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/condition.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/surgery.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/family_history.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/insurance_provider.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/insurance_policy.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/visit.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/visit_summary.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/patient_note.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/patient_department.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/models/consent.py` | model | CRUD | `app/models/user.py` | role-match |
| `app/schemas/patient.py` | schema | transform | `app/schemas/auth.py` | exact |
| `app/schemas/medical_history.py` | schema | transform | `app/schemas/auth.py` | exact |
| `app/schemas/insurance.py` | schema | transform | `app/schemas/auth.py` | exact |
| `app/schemas/visit.py` | schema | transform | `app/schemas/auth.py` | exact |
| `app/schemas/search.py` | schema | transform | `app/schemas/auth.py` | exact |
| `app/services/patient.py` | service | CRUD | `app/services/rbac.py` | exact |
| `app/services/mrn.py` | service | transform | `app/services/rbac.py` | role-match |
| `app/services/medical_history.py` | service | CRUD | `app/services/rbac.py` | exact |
| `app/services/insurance.py` | service | CRUD | `app/services/rbac.py` | role-match |
| `app/services/visit.py` | service | CRUD | `app/services/rbac.py` | exact |
| `app/services/patient_search.py` | service | transform | `app/services/audit.py` | role-match |
| `app/api/v1/patients.py` | controller | request-response | `app/api/v1/auth.py` | exact |
| `app/api/v1/medical_history.py` | controller | request-response | `app/api/v1/auth.py` | exact |
| `app/api/v1/insurance.py` | controller | request-response | `app/api/v1/auth.py` | exact |
| `app/api/v1/visits.py` | controller | request-response | `app/api/v1/auth.py` | exact |
| `app/api/v1/patient_search.py` | controller | request-response | `app/api/v1/auth.py` | exact |
| `app/templates/patients/list.html` | template | request-response | `app/templates/admin/roles.html` | exact |
| `app/templates/patients/register.html` | template | request-response | `app/templates/admin/roles.html` | role-match |
| `app/templates/patients/profile.html` | template | request-response | `app/templates/admin/audit.html` | role-match |
| `app/templates/patients/medical_history.html` | template | request-response | `app/templates/admin/roles.html` | role-match |
| `app/templates/patients/insurance.html` | template | request-response | `app/templates/admin/roles.html` | role-match |
| `app/templates/patients/visits.html` | template | request-response | `app/templates/admin/audit.html` | role-match |
| `app/templates/components/allergy_banner.html` | template | — | `app/templates/admin/roles.html` | partial |
| `app/templates/components/patient_card.html` | template | — | `app/templates/admin/roles.html` | partial |
| `app/templates/components/search_filters.html` | template | — | `app/templates/admin/roles.html` | partial |
| `app/templates/components/visit_timeline.html` | template | — | `app/templates/admin/audit.html` | partial |
| `app/seeds/insurance_providers.py` | seed | batch | `app/seeds/roles.py` | exact |
| `alembic/versions/xxxx_add_patient_management_tables.py` | migration | batch | `alembic/versions/e1250935c5f1_initial_auth_tables.py` | exact |
| `app/models/__init__.py` (modify) | config | — | — | existing |
| `app/api/v1/router.py` (modify) | config | — | — | existing |
| `tests/conftest.py` (modify) | test-infra | — | — | existing |

## Pattern Assignments

### `app/models/patient.py` (model, CRUD)

**Analog:** `app/models/user.py`

**Imports pattern** (lines 1-11):
```python
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Date, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
```

**Model structure** (lines 18-57):
```python
class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'deceased')",
            name="ck_patient_status",
        ),
        # GIN index for pg_trgm search — added in migration, not model args
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mrn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(5), nullable=True)
    nin: Mapped[str | None] = mapped_column(String(11), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    # Structured address (D-46)
    address_street: Mapped[str] = mapped_column(String(255), nullable=False)
    address_city: Mapped[str] = mapped_column(String(100), nullable=False)
    address_state: Mapped[str] = mapped_column(String(100), nullable=False)
    address_lga: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    address_landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships (use TYPE_CHECKING to avoid circular imports)
    emergency_contacts: Mapped[list["EmergencyContact"]] = relationship(
        back_populates="patient", foreign_keys="[EmergencyContact.patient_id]",
    )
    next_of_kin: Mapped[list["NextOfKin"]] = relationship(
        back_populates="patient", foreign_keys="[NextOfKin.patient_id]",
    )
    # ... more relationships for allergies, conditions, etc.
```

**Key pattern rules:**
- UUID PK with `default=uuid.uuid4`
- `Mapped[T]` style (SQLAlchemy 2.0)
- `created_at` / `updated_at` with `server_default=func.now()`
- CheckConstraint for status enums
- All relationships use `TYPE_CHECKING` guard
- Every nullable field has `nullable=True` explicitly

---

### `app/models/allergy.py` (model, CRUD — append-only)

**Analog:** `app/models/user.py` (structure), but with append-only semantics per D-11

Same UUID PK / timestamps pattern. Key additions for medical history models:
```python
class Allergy(Base):
    __tablename__ = "allergies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # mild/moderate/severe/life-threatening
    reaction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/corrected/resolved
    icd10_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cross_reactivity_flags: Mapped[str | None] = mapped_column(String(200), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified")
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # patient-reported/clinical/imported
    corrected_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("allergies.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

**Same pattern applies to:** `condition.py`, `surgery.py`, `family_history.py` — each with type-specific fields but same base structure (UUID PK, patient_id FK, timestamps, source, status).

---

### `app/services/patient.py` (service, CRUD)

**Analog:** `app/services/rbac.py`

**Imports pattern** (lines 1-20 from rbac.py):
```python
from __future__ import annotations

import logging
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.services.audit import AuditService

logger = logging.getLogger(__name__)
```

**Core pattern — all methods are `@staticmethod`, async, accept `db: AsyncSession`, call `flush()` not `commit()`:**
```python
class PatientService:
    """Patient registration, CRUD, and management."""

    @staticmethod
    async def register_patient(
        db: AsyncSession,
        data: PatientCreate,
        created_by: uuid.UUID,
    ) -> Patient:
        """Register a new patient with MRN auto-generation."""
        # 1. Duplicate detection (D-53)
        existing = await PatientService._check_duplicate(db, data)
        if existing:
            raise ValueError(
                f"Possible duplicate: {existing.first_name} {existing.last_name} "
                f"(DOB: {existing.date_of_birth})"
            )

        # 2. Generate MRN via MRNService
        from app.services.mrn import MRNService
        mrn = await MRNService.generate_mrn(db)

        # 3. Create patient
        patient = Patient(mrn=mrn, **data.model_dump())
        db.add(patient)
        await db.flush()

        # 4. Audit log — uses AuditService.log_event pattern from rbac.py lines 158-170
        await AuditService.log_event(
            db,
            user_id=created_by,
            action="patient_registered",
            resource="patient",
            resource_id=str(patient.id),
            patient_id=patient.id,
            why="New patient registration",
        )
        await db.flush()
        return patient

    @staticmethod
    async def _check_duplicate(
        db: AsyncSession,
        data: PatientCreate,
    ) -> Patient | None:
        """Check for existing patient with same name + DOB (D-53)."""
        result = await db.execute(
            select(Patient).where(
                and_(
                    Patient.first_name == data.first_name,
                    Patient.last_name == data.last_name,
                    Patient.date_of_birth == data.date_of_birth,
                )
            )
        )
        return result.scalar_one_or_none()
```

**Service method signature pattern** (from rbac.py lines 100-107, 268-275):
- `@staticmethod` on every method
- `async def method_name(db: AsyncSession, ..., created_by: uuid.UUID) -> ReturnType:`
- Always call `await db.flush()` before returning
- Never call `await db.commit()`
- Log via `AuditService.log_event()` for every mutation
- Use `logger.info()` for non-audit operational logging

**Error handling pattern** (from rbac.py lines 115-137):
```python
        # Raise ValueError for business logic errors — API layer catches these
        raise ValueError("Role not found")
        raise ValueError("User already has this role")
```

---

### `app/services/mrn.py` (service, transform)

**Analog:** `app/services/rbac.py` (structural pattern only — unique logic)

Uses PostgreSQL sequences for MRN generation. Follows same @staticmethod/async/flush pattern:
```python
class MRNService:
    """Generate unique MRNs using PostgreSQL sequences."""

    @staticmethod
    async def generate_mrn(
        db: AsyncSession,
        facility_prefix: str = "LAG",
    ) -> str:
        """Generate next MRN using PostgreSQL nextval()."""
        from sqlalchemy import text
        seq_name = f"mrn_seq_{facility_prefix.lower()}"
        # Ensure sequence exists (idempotent)
        await db.execute(
            text(f"""
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = '{seq_name}') THEN
                        CREATE SEQUENCE {seq_name} START 1;
                    END IF;
                END $$;
            """)
        )
        result = await db.execute(text(f"SELECT nextval('{seq_name}')"))
        next_val = result.scalar()
        return f"{facility_prefix}-{next_val:06d}"

    @staticmethod
    async def validate_mrn_format(mrn: str) -> bool:
        import re
        return bool(re.match(r"^[A-Z]{2,5}-\d{6}$", mrn))
```

---

### `app/services/insurance.py` (service, CRUD with state machine)

**Analog:** `app/services/rbac.py` (structural pattern) + state machine from RESEARCH.md

```python
class InsuranceService:
    VALID_TRANSITIONS = {
        "pending": ["verified", "expired"],
        "verified": ["active", "expired"],
        "active": ["expired"],
        "expired": [],
    }

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        policy_id: uuid.UUID,
        new_status: str,
        changed_by: uuid.UUID,
    ) -> InsurancePolicy:
        """Transition insurance policy status with validation."""
        policy = await db.get(InsurancePolicy, policy_id)
        if policy is None:
            raise ValueError("Policy not found")

        valid = InsuranceService.VALID_TRANSITIONS.get(policy.status, [])
        if new_status not in valid:
            raise ValueError(
                f"Cannot transition from '{policy.status}' to '{new_status}'. "
                f"Valid transitions: {valid}"
            )

        old_status = policy.status
        policy.status = new_status
        # Set timestamps based on transition
        if new_status == "verified":
            policy.verified_at = datetime.now(UTC)
            policy.verified_by = changed_by
        elif new_status == "active":
            policy.activated_at = datetime.now(UTC)
        elif new_status == "expired":
            policy.expired_at = datetime.now(UTC)

        await AuditService.log_event(
            db, user_id=changed_by,
            action="insurance_status_changed",
            resource="insurance_policy",
            resource_id=str(policy.id),
            patient_id=policy.patient_id,
            metadata={"old_status": old_status, "new_status": new_status},
        )
        await db.flush()
        return policy
```

---

### `app/services/patient_search.py` (service, transform)

**Analog:** `app/services/audit.py` (search_logs pattern at lines 155-204)

```python
class PatientSearchService:
    @staticmethod
    async def search_patients(
        db: AsyncSession,
        query: str,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Patient], int]:
        """Search patients by name, MRN, phone using pg_trgm."""
        if len(query) < 4:
            raise ValueError("Search query must be at least 4 characters")

        search_pattern = f"%{query}%"
        stmt = (
            select(Patient)
            .where(
                or_(
                    Patient.mrn.ilike(search_pattern),
                    func.similarity(Patient.first_name, query) > 0.3,
                    func.similarity(Patient.last_name, query) > 0.3,
                    Patient.phone.ilike(search_pattern),
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                )
            )
            .order_by(
                func.greatest(
                    func.similarity(Patient.first_name, query),
                    func.similarity(Patient.last_name, query),
                ).desc()
            )
        )

        # Count + paginate — same pattern as AuditService.search_logs lines 187-202
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar()

        offset = (page - 1) * page_size
        result = await db.execute(stmt.offset(offset).limit(page_size))
        patients = list(result.scalars().all())

        # D-68: Audit every search
        await AuditService.log_event(
            db, user_id=user_id,
            action="patient_search",
            resource="patient",
            metadata={"query": query, "results_count": total, "page": page},
            why="Patient search",
        )

        return patients, total
```

---

### `app/api/v1/patients.py` (controller, request-response)

**Analog:** `app/api/v1/auth.py`

**Imports pattern** (lines 1-31 from auth.py):
```python
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.middleware.permission import require_permission
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services.patient import PatientService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])
```

**Endpoint pattern** (from auth.py lines 43-99, 238-263):
```python
@router.post("/", response_model=PatientResponse, status_code=201)
async def register_patient(
    body: PatientCreate,
    current_user: CurrentUser = Depends(require_permission("patient", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Register a new patient with demographics and auto-generated MRN."""
    try:
        patient = await PatientService.register_patient(db, body, current_user.id)
        await db.commit()
        return PatientResponse.model_validate(patient)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=list[PatientResponse])
async def list_patients(
    current_user: CurrentUser = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 50,
):
    """List patients with pagination."""
    patients, total = await PatientService.list_patients(db, page=page, page_size=page_size)
    return [PatientResponse.model_validate(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: CurrentUser = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single patient by ID."""
    patient = await PatientService.get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)
```

**Key rules:**
- `router = APIRouter(prefix="/...", tags=["..."])`
- `CurrentUser = Depends(require_permission("resource", "action"))` for auth
- `db: AsyncSession = Depends(get_db)` for database
- Service call → `await db.commit()` in endpoint (NOT in service)
- `try/except ValueError` → `HTTPException(status_code=409)` for business errors
- `response_model=...` on every endpoint

**Registration for router** (modify `app/api/v1/router.py`):
```python
from app.api.v1.patients import router as patients_router
router.include_router(patients_router)
```

---

### `app/schemas/patient.py` (schema, transform)

**Analog:** `app/schemas/auth.py`

**Pattern** (from auth.py lines 1-49):
```python
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Literal["Male", "Female"]  # D-45: binary for Nigerian context
    phone: str = Field(..., pattern=r"^(\+234|0)[789]\d{9}$")  # D-47
    email: EmailStr | None = None
    blood_group: str | None = None
    nin: str | None = None
    preferred_language: str | None = None
    address_street: str = Field(..., min_length=1, max_length=255)
    address_city: str = Field(..., min_length=1, max_length=100)
    address_state: str = Field(..., min_length=1, max_length=100)
    address_lga: str | None = None
    address_postal_code: str | None = None
    address_landmark: str | None = None


class PatientUpdate(BaseModel):
    """Partial update — all fields optional."""
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_lga: str | None = None
    address_postal_code: str | None = None
    address_landmark: str | None = None


class PatientResponse(BaseModel):
    id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: str
    email: str | None = None
    blood_group: str | None = None
    nin: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Key rules:**
- `BaseModel` for all schemas
- `{Entity}Create` / `{Entity}Update` / `{Entity}Response` naming convention
- `model_config = ConfigDict(from_attributes=True)` on Response schemas
- `Field(...)` with validation for required fields
- `Literal[...]` for enum-like constrained values
- IDs returned as `str` (UUID serialized)

---

### `app/seeds/insurance_providers.py` (seed, batch)

**Analog:** `app/seeds/roles.py`

**Structure** (from roles.py lines 1-457):
```python
"""Seed Nigerian insurance providers for HMS.

Usage:
    python -m app.seeds.insurance_providers
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.insurance_provider import InsuranceProvider


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    provider_type: str  # NHIS, HMO, Private, Corporate, Military, Tertiary
    short_code: str
    website: str | None = None


PROVIDER_SPECS: list[ProviderSpec] = [
    ProviderSpec("National Health Insurance Scheme", "NHIS", "NHIS", "https://nhis.gov.ng"),
    ProviderSpec("Hygeia HMO", "HMO", "HYG", "https://hygeiahmo.com"),
    ProviderSpec("Leadway Health", "HMO", "LDW", "https://leadway.com"),
    ProviderSpec("AIICO Insurance Health", "HMO", "AII", "https://aiicoplc.com"),
    ProviderSpec("Reliance HMO", "HMO", "RLH", "https://reliancehmo.com"),
    ProviderSpec("AXA Mansard Health", "HMO", "AXM", "https://mansard.com"),
    ProviderSpec("Cornerstone Insurance Health", "HMO", "COR", "https://cornerstone.com.ng"),
    ProviderSpec("Defence Health Insurance Scheme", "Military", "DHIS"),
    ProviderSpec("Police Health Insurance", "Military", "PHI"),
    ProviderSpec("Lagos State Health Management Agency", "Tertiary", "LASHMA"),
]


async def seed() -> None:
    """Run the seed: idempotent insert of providers."""
    async with async_session() as session:
        async with session.begin():
            existing = (
                await session.execute(select(InsuranceProvider))
            ).scalars().all()
            existing_names = {p.name for p in existing}

            for spec in PROVIDER_SPECS:
                if spec.name not in existing_names:
                    session.add(InsuranceProvider(
                        name=spec.name,
                        provider_type=spec.provider_type,
                        short_code=spec.short_code,
                        website=spec.website,
                    ))

            await session.flush()

    print(f"Seeded {len(PROVIDER_SPECS)} insurance providers")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
```

**Key rules (from roles.py):**
- `@dataclass(frozen=True)` for spec definitions
- Idempotent: check existing before inserting
- `async_session()` context manager with `session.begin()`
- `await session.flush()` not commit (the `begin()` context manager commits)
- `if __name__ == "__main__": main()` entry point
- `asyncio.run(seed())` for async execution

---

### `alembic/versions/xxxx_add_patient_management_tables.py` (migration, batch)

**Analog:** `alembic/versions/e1250935c5f1_initial_auth_tables.py`

**Pattern** (from initial migration lines 1-170):
```python
"""add_patient_management_tables

Revision ID: a3b4c5d6e7f8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create patients table
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mrn", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # GIN indexes for pg_trgm search
    op.execute("""
        CREATE INDEX ix_patient_name_trgm ON patients
        USING gin ((first_name || ' ' || last_name) gin_trgm_ops)
    """)
    op.execute("""
        CREATE INDEX ix_patient_mrn_trgm ON patients
        USING gin (mrn gin_trgm_ops)
    """)

    # Add FK constraints to existing tables
    op.alter_column(
        "audit_logs", "patient_id",
        sa.ForeignKey("patients.id", ondelete="SET NULL"),
    )

    # Create remaining tables (allergies, conditions, etc.)


def downgrade() -> None:
    op.drop_table("patients")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
```

**Key rules (from initial migration):**
- 12-char hex revision ID (e.g., `a3b4c5d6e7f8`)
- `down_revision` references the latest migration
- `postgresql.UUID(as_uuid=True)` for UUID columns
- `server_default=sa.func.now()` for timestamps
- `op.create_table()` with full column definitions
- FK constraints added via `op.alter_column()` for existing tables

---

### `app/templates/patients/list.html` (template, request-response)

**Analog:** `app/templates/admin/roles.html`

**HTML structure** (from roles.html lines 1-253):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Management — HMS</title>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <style>
        /* Same base styles as roles.html */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #f5f5f5; color: #333; }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        /* ... same card, table, badge, btn, form patterns from roles.html ... */
    </style>
</head>
<body>
    <div class="container">
        <h1>Patient Management</h1>
        <div id="notification"></div>

        <!-- Split view layout (D-62) -->
        <div style="display: flex; gap: 1rem;">
            <!-- Left: Patient list/search -->
            <div style="flex: 1;">
                <div class="card">
                    <input type="text" id="patient-search"
                           placeholder="Search patients (min 4 chars)..."
                           hx-get="/api/v1/patients/search"
                           hx-trigger="keyup changed delay:300ms"  /* D-16: 300ms debounce */
                           hx-vals='js:{"q": document.getElementById("patient-search").value}'
                           hx-target="#patient-list"
                           hx-swap="innerHTML">
                </div>
                <div class="card" id="patient-list">
                    <p class="empty-state">Type to search patients...</p>
                </div>
            </div>
            <!-- Right: Patient detail -->
            <div style="flex: 2;">
                <div class="card" id="patient-detail">
                    <p class="empty-state">Select a patient to view details</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Same tab/swap/esc patterns from roles.html lines 126-253
    </script>
</body>
</html>
```

**HTMX pattern** (from roles.html lines 63-69, 76-100):
```html
<!-- hx-get loads data on trigger -->
<div class="card"
     hx-get="/api/v1/rbac/roles"
     hx-trigger="load"
     hx-swap="innerHTML">
    <p>Loading roles...</p>
</div>

<!-- hx-post submits form -->
<form id="create-role-form"
      hx-post="/api/v1/rbac/roles"
      hx-target="#notification"
      hx-swap="innerHTML"
      hx-on::after-request="if(event.detail.successful){this.reset();}">
```

**Key rules (from roles.html and audit.html):**
- HTMX via CDN: `<script src="https://unpkg.com/htmx.org@2.0.4"></script>`
- `hx-get` / `hx-post` with `hx-target` and `hx-swap="innerHTML"`
- `hx-trigger="load"` for initial data fetch
- `hx-trigger="keyup changed delay:300ms"` for search debounce
- Tabs via JS `showTab()` function (roles.html lines 127-132)
- `htmx:afterSwap` event listener for rendering JSON responses (roles.html lines 140-179)
- `esc()` helper function for XSS prevention (roles.html lines 247-251)
- CSS classes: `.card`, `.badge-*`, `.btn`, `.btn-primary`, `.form-group`, `.form-row`, `.tabs`, `.tab`, `.empty-state`, `.alert`

---

### `tests/conftest.py` (modify — add patient fixtures)

**Pattern from existing conftest.py** (lines 320-394):
```python
# Add to _TABLES_IN_DELETE_ORDER (reverse FK order):
# Patient models before User

async def create_patient(
    db: AsyncSession,
    first_name: str = "Test",
    last_name: str = "Patient",
    mrn: str = "LAG-000001",
    date_of_birth: date | None = None,
    gender: str = "Male",
    phone: str = "08012345678",
    status: str = "active",
    **kwargs: Any,
) -> Patient:
    if date_of_birth is None:
        date_of_birth = date(1990, 1, 1)
    patient = Patient(
        mrn=mrn,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        phone=phone,
        status=status,
        address_street="123 Test St",
        address_city="Lagos",
        address_state="Lagos",
        **kwargs,
    )
    db.add(patient)
    await db.flush()
    return patient


@pytest.fixture()
async def sample_patient(db_session: AsyncSession) -> Patient:
    """Create a sample patient for tests."""
    patient = await create_patient(db_session)
    await db_session.commit()
    return patient
```

---

## Shared Patterns

### Authentication / Authorization
**Source:** `app/middleware/permission.py` (lines 17-52)
**Apply to:** All controller files (patients.py, medical_history.py, insurance.py, visits.py, patient_search.py)
```python
from app.middleware.permission import require_permission

# Single permission check
@router.get("/", dependencies=[Depends(require_permission("patient", "read"))])

# Or as parameter default
async def get_patient(
    patient_id: str,
    current_user: CurrentUser = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
):
```

### Error Handling
**Source:** `app/api/v1/auth.py` (lines 77-99) + `app/services/rbac.py` (lines 115-137)
**Apply to:** All controller and service files
```python
# Services raise ValueError for business logic errors
raise ValueError("Patient not found")
raise ValueError(f"Cannot transition from '{current}' to '{new}'")

# Controllers catch ValueError and convert to HTTPException
try:
    result = await SomeService.do_thing(db, data, user_id)
    await db.commit()
    return ResultResponse.model_validate(result)
except ValueError as e:
    raise HTTPException(status_code=409, detail=str(e))
```

### Audit Logging
**Source:** `app/services/audit.py` (lines 26-91)
**Apply to:** All service files that perform mutations or sensitive reads
```python
await AuditService.log_event(
    db,
    user_id=current_user_id,       # Who
    action="patient_registered",    # What
    resource="patient",             # Resource type
    resource_id=str(patient.id),    # Specific resource
    patient_id=patient.id,          # Patient context (critical for HIPAA)
    why="New patient registration", # Why (in metadata)
    metadata={"extra": "data"},     # Additional context
)
```

### Database Session Pattern
**Source:** `app/core/database.py` (lines 1-23)
**Apply to:** All API endpoints
```python
# Dependency injection
db: AsyncSession = Depends(get_db)

# Services always flush, never commit
await db.flush()  # In service

# Controllers always commit after service call
await db.commit()  # In controller
```

### Schema Validation
**Source:** `app/schemas/auth.py` (lines 1-49)
**Apply to:** All schema files
```python
from pydantic import BaseModel, ConfigDict, Field

class EntityCreate(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)

class EntityResponse(BaseModel):
    id: str
    field: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### HTMX Template Structure
**Source:** `app/templates/admin/roles.html` (lines 1-253) + `app/templates/admin/audit.html`
**Apply to:** All patient template files
```html
<!-- Base structure -->
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<div id="notification"></div>
<div class="tabs">...</div>

<!-- HTMX load pattern -->
<div class="card"
     hx-get="/api/v1/..."
     hx-trigger="load"
     hx-swap="innerHTML">
    <p>Loading...</p>
</div>

<!-- Tab switching -->
<script>
function showTab(name) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + name).style.display = 'block';
    event.target.classList.add('active');
}
</script>
```

### Test Fixtures
**Source:** `tests/conftest.py` (lines 320-394)
**Apply to:** All test files
```python
async def create_entity(
    db: AsyncSession,
    field: str = "default",
    **kwargs: Any,
) -> Entity:
    entity = Entity(field=field, **kwargs)
    db.add(entity)
    await db.flush()
    return entity

@pytest.fixture()
async def sample_entity(db_session: AsyncSession) -> Entity:
    entity = await create_entity(db_session)
    await db_session.commit()
    return entity
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app/services/mrn.py` | service | transform | PostgreSQL sequence-based MRN generation is unique; no existing analog for sequence management |
| `app/templates/components/allergy_banner.html` | template | — | No existing component template; create from scratch using card/badge CSS patterns from roles.html |
| `app/templates/components/patient_card.html` | template | — | No existing component template; create from scratch using card/table CSS patterns |
| `app/templates/components/search_filters.html` | template | — | No existing component template; create from scratch using form patterns from audit.html |
| `app/templates/components/visit_timeline.html` | template | — | No existing component template; create from scratch using table/timeline CSS patterns |

## Metadata

**Analog search scope:** `app/models/`, `app/services/`, `app/api/v1/`, `app/schemas/`, `app/seeds/`, `app/templates/`, `app/middleware/`, `app/core/`, `alembic/versions/`, `tests/`
**Files scanned:** 30+ existing files
**Pattern extraction date:** 2026-07-15
