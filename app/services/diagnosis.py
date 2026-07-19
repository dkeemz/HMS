"""Diagnosis service."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisUpdate
from app.services.audit import AuditService


class DiagnosisService:
    @staticmethod
    async def create(
        db: AsyncSession, data: DiagnosisCreate, doctor_id: uuid.UUID
    ) -> Diagnosis:
        dx = Diagnosis(
            visit_id=data.visit_id,
            patient_id=data.patient_id,
            doctor_id=doctor_id,
            icd_code=data.icd_code,
            icd_version=data.icd_version,
            description=data.description,
            diagnosis_type=data.diagnosis_type,
            onset_date=data.onset_date,
            notes=data.notes,
        )
        db.add(dx)
        await db.flush()
        await db.refresh(dx)
        await AuditService.log(
            db, "diagnosis", dx.id, "create",
            detail=f"Diagnosis {data.icd_code} recorded for visit {data.visit_id}",
        )
        return dx

    @staticmethod
    async def get(db: AsyncSession, dx_id: uuid.UUID) -> Diagnosis | None:
        result = await db.execute(
            select(Diagnosis).where(Diagnosis.id == dx_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_visit(
        db: AsyncSession, visit_id: uuid.UUID
    ) -> Sequence[Diagnosis]:
        result = await db.execute(
            select(Diagnosis)
            .where(Diagnosis.visit_id == visit_id)
            .order_by(Diagnosis.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_patient(
        db: AsyncSession, patient_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[Diagnosis], int]:
        count_q = select(func.count()).select_from(Diagnosis).where(
            Diagnosis.patient_id == patient_id
        )
        total = (await db.execute(count_q)).scalar() or 0

        result = await db.execute(
            select(Diagnosis)
            .where(Diagnosis.patient_id == patient_id)
            .order_by(Diagnosis.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def update(
        db: AsyncSession, dx: Diagnosis, data: DiagnosisUpdate
    ) -> Diagnosis:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(dx, field, value)
        await db.flush()
        await db.refresh(dx)
        return dx

    @staticmethod
    async def delete(db: AsyncSession, dx: Diagnosis) -> None:
        await db.delete(dx)
        await db.flush()

    @staticmethod
    async def search_icd(
        db: AsyncSession, query: str, version: str = "10"
    ) -> Sequence[Diagnosis]:
        """Search ICD codes from existing diagnoses (for autocomplete)."""
        result = await db.execute(
            select(Diagnosis)
            .where(
                Diagnosis.icd_version == version,
                Diagnosis.icd_code.ilike(f"%{query}%")
                | Diagnosis.description.ilike(f"%{query}%"),
            )
            .group_by(Diagnosis.icd_code, Diagnosis.description)
            .limit(20)
        )
        return list(result.scalars().all())
