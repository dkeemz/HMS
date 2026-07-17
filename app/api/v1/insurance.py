from __future__ import annotations

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.models.user import User
from app.schemas.insurance import (
    InsurancePolicyCreate,
    InsurancePolicyResponse,
    InsuranceProviderResponse,
    InsuranceStatusTransition,
)
from app.services.insurance import InsuranceService

router = APIRouter(
    prefix="/patients/{patient_id}/insurance",
    tags=["Insurance"],
)

providers_router = APIRouter(
    prefix="/insurance",
    tags=["Insurance"],
)


@router.post(
    "",
    response_model=InsurancePolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_insurance_policy(
    patient_id: uuid.UUID,
    data: InsurancePolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "update")),
) -> InsurancePolicyResponse:
    policy = await InsuranceService.create_policy(db, patient_id, data, current_user.id)
    await db.commit()
    return policy


@router.get("", response_model=List[InsurancePolicyResponse])
async def list_insurance_policies(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[InsurancePolicyResponse]:
    policies = await InsuranceService.get_policies_for_patient(db, patient_id)
    return policies


@router.get("/expired", response_model=List[InsurancePolicyResponse])
async def get_expired_policies(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[InsurancePolicyResponse]:
    policies = await InsuranceService.get_expired_policies(db)
    return [p for p in policies if p.patient_id == patient_id]


@router.get("/{policy_id}", response_model=InsurancePolicyResponse)
async def get_insurance_policy(
    patient_id: uuid.UUID,
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
) -> InsurancePolicyResponse:
    policy = await InsuranceService.get_policy(db, policy_id)
    if policy is None or policy.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post(
    "/{policy_id}/transition",
    response_model=InsurancePolicyResponse,
)
async def transition_insurance_status(
    patient_id: uuid.UUID,
    policy_id: uuid.UUID,
    data: InsuranceStatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "update")),
) -> InsurancePolicyResponse:
    try:
        policy = await InsuranceService.transition_status(
            db, policy_id, data.new_status, current_user.id, data.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    await db.commit()
    return policy


@router.post("/{policy_id}/upload-card")
async def upload_insurance_card(
    patient_id: uuid.UUID,
    policy_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "update")),
):
    policy = await InsuranceService.get_policy(db, policy_id)
    if policy is None or policy.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Policy not found")

    upload_dir = os.path.join("uploads", "insurance")
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"{policy_id}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    policy.card_image_url = filepath
    await db.flush()
    await db.commit()
    return {"status": "ok", "path": filepath}


@providers_router.get("/providers", response_model=List[InsuranceProviderResponse])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[InsuranceProviderResponse]:
    providers = await InsuranceService.get_providers(db)
    return providers
