from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medication import Medication
from app.schemas.medication import MedicationCreate, MedicationUpdate


class MedicationService:
    @staticmethod
    async def create(db: AsyncSession, data: MedicationCreate, prescribed_by: uuid.UUID | None = None) -> Medication:
        med = Medication(**data.model_dump(exclude={"prescribed_by"}), prescribed_by=prescribed_by)
        db.add(med)
        await db.flush()
        await db.refresh(med)
        return med

    @staticmethod
    async def get(db: AsyncSession, medication_id: uuid.UUID) -> Medication | None:
        result = await db.execute(select(Medication).where(Medication.id == medication_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_patient(db: AsyncSession, patient_id: uuid.UUID, active_only: bool = False) -> list[Medication]:
        stmt = select(Medication).where(Medication.patient_id == patient_id).order_by(Medication.created_at.desc())
        if active_only:
            stmt = stmt.where(Medication.status == "active")
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, medication_id: uuid.UUID, data: MedicationUpdate) -> Medication | None:
        med = await MedicationService.get(db, medication_id)
        if not med:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(med, k, v)
        await db.flush()
        await db.refresh(med)
        return med

    @staticmethod
    async def delete(db: AsyncSession, medication_id: uuid.UUID) -> bool:
        med = await MedicationService.get(db, medication_id)
        if not med:
            return False
        await db.delete(med)
        await db.flush()
        return True
