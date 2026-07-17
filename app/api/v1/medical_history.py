from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.models.user import User
from app.schemas.medical_history import (
    AllergyCreate,
    AllergyResponse,
    AllergyUpdate,
    ConditionCreate,
    ConditionResponse,
    ConditionUpdate,
    FamilyHistoryCreate,
    FamilyHistoryResponse,
    FamilyHistoryUpdate,
    SurgeryCreate,
    SurgeryResponse,
    SurgeryUpdate,
)
from app.services.medical_history import MedicalHistoryService

router = APIRouter(prefix="/patients/{patient_id}/medical-history", tags=["Medical History"])


async def get_medical_history_service(db: AsyncSession = Depends(get_db)) -> MedicalHistoryService:
    return MedicalHistoryService(db)


# Allergy endpoints
@router.get("/allergies", response_model=List[AllergyResponse])
async def list_allergies(
    patient_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[AllergyResponse]:
    return await service.get_allergies(patient_id)


@router.post("/allergies", response_model=AllergyResponse, status_code=status.HTTP_201_CREATED)
async def create_allergy(
    patient_id: uuid.UUID,
    data: AllergyCreate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "create")),
) -> AllergyResponse:
    return await service.create_allergy(patient_id, data, current_user.id)


@router.put("/allergies/{allergy_id}", response_model=AllergyResponse)
async def update_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    data: AllergyUpdate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> AllergyResponse:
    allergy = await service.get_allergy(allergy_id)
    if not allergy or allergy.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
    return await service.update_allergy(allergy, data)


@router.delete("/allergies/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> None:
    allergy = await service.get_allergy(allergy_id)
    if not allergy or allergy.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
    await service.delete_allergy(allergy)


# Condition endpoints
@router.get("/conditions", response_model=List[ConditionResponse])
async def list_conditions(
    patient_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[ConditionResponse]:
    return await service.get_conditions(patient_id)


@router.post("/conditions", response_model=ConditionResponse, status_code=status.HTTP_201_CREATED)
async def create_condition(
    patient_id: uuid.UUID,
    data: ConditionCreate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "create")),
) -> ConditionResponse:
    return await service.create_condition(patient_id, data, current_user.id)


@router.put("/conditions/{condition_id}", response_model=ConditionResponse)
async def update_condition(
    patient_id: uuid.UUID,
    condition_id: uuid.UUID,
    data: ConditionUpdate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> ConditionResponse:
    condition = await service.get_condition(condition_id)
    if not condition or condition.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")
    return await service.update_condition(condition, data)


@router.delete("/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_condition(
    patient_id: uuid.UUID,
    condition_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> None:
    condition = await service.get_condition(condition_id)
    if not condition or condition.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")
    await service.delete_condition(condition)


# Surgery endpoints
@router.get("/surgeries", response_model=List[SurgeryResponse])
async def list_surgeries(
    patient_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[SurgeryResponse]:
    return await service.get_surgeries(patient_id)


@router.post("/surgeries", response_model=SurgeryResponse, status_code=status.HTTP_201_CREATED)
async def create_surgery(
    patient_id: uuid.UUID,
    data: SurgeryCreate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "create")),
) -> SurgeryResponse:
    return await service.create_surgery(patient_id, data, current_user.id)


@router.put("/surgeries/{surgery_id}", response_model=SurgeryResponse)
async def update_surgery(
    patient_id: uuid.UUID,
    surgery_id: uuid.UUID,
    data: SurgeryUpdate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> SurgeryResponse:
    surgery = await service.get_surgery(surgery_id)
    if not surgery or surgery.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgery not found")
    return await service.update_surgery(surgery, data)


@router.delete("/surgeries/{surgery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_surgery(
    patient_id: uuid.UUID,
    surgery_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> None:
    surgery = await service.get_surgery(surgery_id)
    if not surgery or surgery.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surgery not found")
    await service.delete_surgery(surgery)


# Family History endpoints
@router.get("/family", response_model=List[FamilyHistoryResponse])
async def list_family_history(
    patient_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[FamilyHistoryResponse]:
    return await service.get_family_history(patient_id)


@router.post("/family", response_model=FamilyHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_family_history(
    patient_id: uuid.UUID,
    data: FamilyHistoryCreate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "create")),
) -> FamilyHistoryResponse:
    return await service.create_family_history(patient_id, data)


@router.put("/family/{item_id}", response_model=FamilyHistoryResponse)
async def update_family_history(
    patient_id: uuid.UUID,
    item_id: uuid.UUID,
    data: FamilyHistoryUpdate,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> FamilyHistoryResponse:
    item = await service.get_family_history_item(item_id)
    if not item or item.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family history item not found")
    return await service.update_family_history(item, data)


@router.delete("/family/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family_history(
    patient_id: uuid.UUID,
    item_id: uuid.UUID,
    service: MedicalHistoryService = Depends(get_medical_history_service),
    current_user: User = Depends(require_permission("patient", "update")),
) -> None:
    item = await service.get_family_history_item(item_id)
    if not item or item.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family history item not found")
    await service.delete_family_history(item)