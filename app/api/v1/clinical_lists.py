from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.schemas.allergy import AllergyCreate, AllergyResponse, AllergyUpdate
from app.schemas.medication import MedicationCreate, MedicationResponse, MedicationUpdate
from app.schemas.problem import ProblemCreate, ProblemResponse, ProblemUpdate
from app.services.allergy import AllergyService
from app.services.medication import MedicationService
from app.services.problem import ProblemService

router = APIRouter(tags=["Clinical Lists"])


# ── Problems ──────────────────────────────────────────────────────────────────

@router.post("/ehr/problems", response_model=ProblemResponse)
async def create_problem(data: ProblemCreate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "create"))):
    return await ProblemService.create(db, data)


@router.get("/ehr/problems/{problem_id}", response_model=ProblemResponse)
async def get_problem(problem_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "read"))):
    problem = await ProblemService.get(db, problem_id)
    if not problem:
        raise HTTPException(404, "Problem not found")
    return problem


@router.get("/ehr/problems/patient/{patient_id}", response_model=list[ProblemResponse])
async def list_patient_problems(patient_id: uuid.UUID, active_only: bool = False, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "read"))):
    return await ProblemService.list_by_patient(db, patient_id, active_only)


@router.patch("/ehr/problems/{problem_id}", response_model=ProblemResponse)
async def update_problem(problem_id: uuid.UUID, data: ProblemUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "update"))):
    problem = await ProblemService.update(db, problem_id, data)
    if not problem:
        raise HTTPException(404, "Problem not found")
    return problem


@router.post("/ehr/problems/{problem_id}/resolve", response_model=ProblemResponse)
async def resolve_problem(problem_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "update"))):
    problem = await ProblemService.resolve(db, problem_id)
    if not problem:
        raise HTTPException(404, "Problem not found")
    return problem


@router.delete("/ehr/problems/{problem_id}")
async def delete_problem(problem_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "delete"))):
    deleted = await ProblemService.delete(db, problem_id)
    if not deleted:
        raise HTTPException(404, "Problem not found")
    return {"detail": "Problem deleted"}


# ── Medications ───────────────────────────────────────────────────────────────

@router.post("/ehr/medications", response_model=MedicationResponse)
async def create_medication(data: MedicationCreate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "create"))):
    return await MedicationService.create(db, data)


@router.get("/ehr/medications/{medication_id}", response_model=MedicationResponse)
async def get_medication(medication_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "read"))):
    med = await MedicationService.get(db, medication_id)
    if not med:
        raise HTTPException(404, "Medication not found")
    return med


@router.get("/ehr/medications/patient/{patient_id}", response_model=list[MedicationResponse])
async def list_patient_medications(patient_id: uuid.UUID, active_only: bool = False, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "read"))):
    return await MedicationService.list_by_patient(db, patient_id, active_only)


@router.patch("/ehr/medications/{medication_id}", response_model=MedicationResponse)
async def update_medication(medication_id: uuid.UUID, data: MedicationUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "update"))):
    med = await MedicationService.update(db, medication_id, data)
    if not med:
        raise HTTPException(404, "Medication not found")
    return med


@router.delete("/ehr/medications/{medication_id}")
async def delete_medication(medication_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "delete"))):
    deleted = await MedicationService.delete(db, medication_id)
    if not deleted:
        raise HTTPException(404, "Medication not found")
    return {"detail": "Medication deleted"}


# ── Allergies ─────────────────────────────────────────────────────────────────

@router.post("/ehr/allergies", response_model=AllergyResponse)
async def create_allergy(data: AllergyCreate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "create"))):
    return await AllergyService.create(db, data)


@router.get("/ehr/allergies/{allergy_id}", response_model=AllergyResponse)
async def get_allergy(allergy_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "read"))):
    allergy = await AllergyService.get(db, allergy_id)
    if not allergy:
        raise HTTPException(404, "Allergy not found")
    return allergy


@router.get("/ehr/allergies/patient/{patient_id}", response_model=list[AllergyResponse])
async def list_patient_allergies(patient_id: uuid.UUID, active_only: bool = False, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "read"))):
    return await AllergyService.list_by_patient(db, patient_id, active_only)


@router.patch("/ehr/allergies/{allergy_id}", response_model=AllergyResponse)
async def update_allergy(allergy_id: uuid.UUID, data: AllergyUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "update"))):
    allergy = await AllergyService.update(db, allergy_id, data)
    if not allergy:
        raise HTTPException(404, "Allergy not found")
    return allergy


@router.delete("/ehr/allergies/{allergy_id}")
async def delete_allergy(allergy_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(require_permission("medical_record", "delete"))):
    deleted = await AllergyService.delete(db, allergy_id)
    if not deleted:
        raise HTTPException(404, "Allergy not found")
    return {"detail": "Allergy deleted"}
