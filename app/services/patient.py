from __future__ import annotations

import logging
import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.patient import EmergencyContact, NextOfKin, Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.audit import AuditService
from app.services.mrn import MRNService

logger = logging.getLogger(__name__)


class PatientService:
    """Patient registration, CRUD, and management."""

    @staticmethod
    async def register_patient(
        db: AsyncSession,
        data: PatientCreate,
        created_by: uuid.UUID,
    ) -> Patient:
        """Register a new patient with MRN auto-generation.

        D-53: Duplicate detection warns on matching name + DOB.
        D-42: Emergency contacts (1-3) stored as separate records.
        D-43: Next of kin stored as separate record.
        """
        # 1. Duplicate detection (D-53)
        existing = await PatientService._check_duplicate(db, data)
        if existing:
            raise ValueError(
                f"Possible duplicate: {existing.first_name} {existing.last_name} "
                f"(DOB: {existing.date_of_birth})"
            )

        # 2. Generate MRN
        mrn = await MRNService.generate_mrn(db)

        # 3. Create patient
        patient_data = data.model_dump(
            exclude={"emergency_contacts", "next_of_kin"}
        )
        patient = Patient(mrn=mrn, **patient_data)
        db.add(patient)
        await db.flush()

        # 4. Create emergency contacts (D-42)
        for ec in data.emergency_contacts:
            contact = EmergencyContact(
                patient_id=patient.id,
                name=ec.name,
                phone=ec.phone,
                relationship=ec.relationship,
            )
            db.add(contact)

        # 5. Create next of kin (D-43)
        nok = data.next_of_kin
        next_of_kin = NextOfKin(
            patient_id=patient.id,
            name=nok.name,
            phone=nok.phone,
            relationship=nok.relationship,
            address=nok.address,
        )
        db.add(next_of_kin)

        # 6. Audit log
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

        # 7. Eagerly load relationships for response serialization
        await db.refresh(patient, ["emergency_contacts", "next_of_kin"])

        logger.info("Registered patient %s (MRN: %s)", patient.id, mrn)
        return patient

    @staticmethod
    async def get_patient(
        db: AsyncSession,
        patient_id: uuid.UUID,
    ) -> Patient | None:
        """Get a patient by ID."""
        result = await db.execute(
            select(Patient)
            .options(
                selectinload(Patient.emergency_contacts),
                selectinload(Patient.next_of_kin),
            )
            .where(Patient.id == patient_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_patients(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Patient], int]:
        """List patients with pagination."""
        count_result = await db.execute(
            select(func.count()).select_from(Patient)
        )
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await db.execute(
            select(Patient)
            .options(
                selectinload(Patient.emergency_contacts),
                selectinload(Patient.next_of_kin),
            )
            .order_by(Patient.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        patients = list(result.scalars().all())
        return patients, total

    @staticmethod
    async def update_patient(
        db: AsyncSession,
        patient_id: uuid.UUID,
        data: PatientUpdate,
        updated_by: uuid.UUID,
    ) -> Patient:
        """Update patient demographics."""
        patient = await PatientService.get_patient(db, patient_id)
        if patient is None:
            raise ValueError("Patient not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)

        await AuditService.log_event(
            db,
            user_id=updated_by,
            action="patient_updated",
            resource="patient",
            resource_id=str(patient.id),
            patient_id=patient.id,
            why="Patient demographics update",
            metadata={"updated_fields": list(update_data.keys())},
        )
        await db.flush()
        await db.refresh(patient, ["emergency_contacts", "next_of_kin"])
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
