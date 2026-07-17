from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.models.user import User
from app.schemas.visit import (
    VisitCreate,
    VisitResponse,
    VisitStatusTransition,
    VisitSummaryResponse,
)
from app.services.visit import VisitService

router = APIRouter(prefix="/patients/{patient_id}/visits", tags=["visits"])


@router.post("/walkin", status_code=status.HTTP_201_CREATED, response_model=VisitResponse)
async def create_walkin_visit(
    patient_id: uuid.UUID,
    body: VisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "update")),
):
    try:
        visit = await VisitService.create_walkin_visit(
            db,
            patient_id=patient_id,
            department_id=uuid.UUID(body.department_id) if body.department_id else None,
            reason=body.reason,
            reason_notes=body.reason_notes,
            created_by=current_user.id,
        )
        await db.commit()
        await db.refresh(visit)
        return visit
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=VisitResponse)
async def create_scheduled_visit(
    patient_id: uuid.UUID,
    body: VisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "update")),
):
    if not body.scheduled_at:
        raise HTTPException(status_code=422, detail="scheduled_at is required for scheduled visits")
    try:
        visit = await VisitService.create_scheduled_visit(
            db,
            patient_id=patient_id,
            department_id=uuid.UUID(body.department_id) if body.department_id else None,
            doctor_id=uuid.UUID(body.doctor_id) if body.doctor_id else None,
            reason=body.reason,
            scheduled_at=body.scheduled_at,
            created_by=current_user.id,
            reason_notes=body.reason_notes,
        )
        await db.commit()
        await db.refresh(visit)
        return visit
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=list[VisitResponse])
async def list_visits(
    patient_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
):
    visits, _total = await VisitService.get_visits_for_patient(db, patient_id, page, page_size)
    return visits


@router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    patient_id: uuid.UUID,
    visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
):
    visit = await VisitService.get_visit(db, visit_id)
    if visit is None or visit.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


@router.post("/{visit_id}/transition", response_model=VisitResponse)
async def transition_visit_status(
    patient_id: uuid.UUID,
    visit_id: uuid.UUID,
    body: VisitStatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "update")),
):
    try:
        visit = await VisitService.transition_status(
            db,
            visit_id=visit_id,
            new_status=body.new_status,
            changed_by=current_user.id,
            reason=body.reason,
        )
        await db.commit()
        await db.refresh(visit)
        return visit
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{visit_id}/summary", response_model=VisitSummaryResponse)
async def get_visit_summary(
    patient_id: uuid.UUID,
    visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
):
    visit = await VisitService.get_visit(db, visit_id)
    if visit is None or visit.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Visit not found")
    if visit.summary is None:
        raise HTTPException(status_code=404, detail="Visit summary not yet generated")
    return visit.summary
