from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allergy import Allergy
from app.schemas.allergy import AllergyCreate, AllergyUpdate


class AllergyService:
    @staticmethod
    async def create(db: AsyncSession, data: AllergyCreate) -> Allergy:
        allergy = Allergy(**data.model_dump())
        db.add(allergy)
        await db.flush()
        await db.refresh(allergy)
        return allergy

    @staticmethod
    async def get(db: AsyncSession, allergy_id: uuid.UUID) -> Allergy | None:
        result = await db.execute(select(Allergy).where(Allergy.id == allergy_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_patient(db: AsyncSession, patient_id: uuid.UUID, active_only: bool = False) -> list[Allergy]:
        stmt = select(Allergy).where(Allergy.patient_id == patient_id).order_by(Allergy.recorded_date.desc())
        if active_only:
            stmt = stmt.where(Allergy.status == "active")
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, allergy_id: uuid.UUID, data: AllergyUpdate) -> Allergy | None:
        allergy = await AllergyService.get(db, allergy_id)
        if not allergy:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(allergy, k, v)
        await db.flush()
        await db.refresh(allergy)
        return allergy

    @staticmethod
    async def delete(db: AsyncSession, allergy_id: uuid.UUID) -> bool:
        allergy = await AllergyService.get(db, allergy_id)
        if not allergy:
            return False
        await db.delete(allergy)
        await db.flush()
        return True
