from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allergy import Allergy
from app.models.condition import Condition
from app.models.family_history import FamilyHistory
from app.models.surgery import Surgery
from app.schemas.medical_history import (
    AllergyCreate,
    AllergyUpdate,
    ConditionCreate,
    ConditionUpdate,
    FamilyHistoryCreate,
    FamilyHistoryUpdate,
    SurgeryCreate,
    SurgeryUpdate,
)


class MedicalHistoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_allergies(self, patient_id: uuid.UUID) -> Sequence[Allergy]:
        result = await self.db.execute(
            select(Allergy).where(Allergy.patient_id == patient_id)
        )
        return list(result.scalars().all())

    async def get_allergy(self, allergy_id: uuid.UUID) -> Optional[Allergy]:
        return await self.db.get(Allergy, allergy_id)

    async def create_allergy(self, patient_id: uuid.UUID, data: AllergyCreate, user_id: Optional[uuid.UUID] = None) -> Allergy:
        allergy = Allergy(patient_id=patient_id, created_by=user_id, **data.model_dump())
        self.db.add(allergy)
        await self.db.flush()
        await self.db.refresh(allergy)
        return allergy

    async def update_allergy(self, allergy: Allergy, data: AllergyUpdate) -> Allergy:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(allergy, field, value)
        await self.db.flush()
        await self.db.refresh(allergy)
        return allergy

    async def delete_allergy(self, allergy: Allergy) -> None:
        await self.db.delete(allergy)
        await self.db.flush()

    async def get_conditions(self, patient_id: uuid.UUID) -> Sequence[Condition]:
        result = await self.db.execute(
            select(Condition).where(Condition.patient_id == patient_id)
        )
        return list(result.scalars().all())

    async def get_condition(self, condition_id: uuid.UUID) -> Optional[Condition]:
        return await self.db.get(Condition, condition_id)

    async def create_condition(self, patient_id: uuid.UUID, data: ConditionCreate, user_id: Optional[uuid.UUID] = None) -> Condition:
        condition = Condition(patient_id=patient_id, created_by=user_id, **data.model_dump())
        self.db.add(condition)
        await self.db.flush()
        await self.db.refresh(condition)
        return condition

    async def update_condition(self, condition: Condition, data: ConditionUpdate) -> Condition:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(condition, field, value)
        await self.db.flush()
        await self.db.refresh(condition)
        return condition

    async def delete_condition(self, condition: Condition) -> None:
        await self.db.delete(condition)
        await self.db.flush()

    async def get_surgeries(self, patient_id: uuid.UUID) -> Sequence[Surgery]:
        result = await self.db.execute(
            select(Surgery).where(Surgery.patient_id == patient_id)
        )
        return list(result.scalars().all())

    async def get_surgery(self, surgery_id: uuid.UUID) -> Optional[Surgery]:
        return await self.db.get(Surgery, surgery_id)

    async def create_surgery(self, patient_id: uuid.UUID, data: SurgeryCreate, user_id: Optional[uuid.UUID] = None) -> Surgery:
        surgery = Surgery(patient_id=patient_id, created_by=user_id, **data.model_dump())
        self.db.add(surgery)
        await self.db.flush()
        await self.db.refresh(surgery)
        return surgery

    async def update_surgery(self, surgery: Surgery, data: SurgeryUpdate) -> Surgery:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(surgery, field, value)
        await self.db.flush()
        await self.db.refresh(surgery)
        return surgery

    async def delete_surgery(self, surgery: Surgery) -> None:
        await self.db.delete(surgery)
        await self.db.flush()

    async def get_family_history(self, patient_id: uuid.UUID) -> Sequence[FamilyHistory]:
        result = await self.db.execute(
            select(FamilyHistory).where(FamilyHistory.patient_id == patient_id)
        )
        return list(result.scalars().all())

    async def get_family_history_item(self, item_id: uuid.UUID) -> Optional[FamilyHistory]:
        return await self.db.get(FamilyHistory, item_id)

    async def create_family_history(self, patient_id: uuid.UUID, data: FamilyHistoryCreate) -> FamilyHistory:
        item = FamilyHistory(patient_id=patient_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update_family_history(self, item: FamilyHistory, data: FamilyHistoryUpdate) -> FamilyHistory:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete_family_history(self, item: FamilyHistory) -> None:
        await self.db.delete(item)
        await self.db.flush()