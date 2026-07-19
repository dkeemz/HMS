"""Vital Signs service."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vital_signs import VitalSign
from app.schemas.vital_signs import VitalSignCreate
from app.services.audit import AuditService


class VitalSignService:
    @staticmethod
    async def record(
        db: AsyncSession, data: VitalSignCreate, recorded_by: uuid.UUID
    ) -> VitalSign:
        vs = VitalSign(
            visit_id=data.visit_id,
            patient_id=data.patient_id,
            recorded_by=recorded_by,
            systolic_bp=data.systolic_bp,
            diastolic_bp=data.diastolic_bp,
            heart_rate=data.heart_rate,
            respiratory_rate=data.respiratory_rate,
            temperature=data.temperature,
            weight_kg=data.weight_kg,
            height_cm=data.height_cm,
            spo2=data.spo2,
            pain_level=data.pain_level,
            notes=data.notes,
        )
        db.add(vs)
        await db.flush()
        await db.refresh(vs)
        await AuditService.log(
            db, "vital_sign", vs.id, "create",
            detail=f"Vitals recorded for visit {data.visit_id}",
        )
        return vs

    @staticmethod
    async def get(db: AsyncSession, vs_id: uuid.UUID) -> VitalSign | None:
        result = await db.execute(
            select(VitalSign).where(VitalSign.id == vs_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_visit(
        db: AsyncSession, visit_id: uuid.UUID
    ) -> Sequence[VitalSign]:
        result = await db.execute(
            select(VitalSign)
            .where(VitalSign.visit_id == visit_id)
            .order_by(VitalSign.recorded_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_patient(
        db: AsyncSession, patient_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[VitalSign], int]:
        count_q = select(func.count()).select_from(VitalSign).where(
            VitalSign.patient_id == patient_id
        )
        total = (await db.execute(count_q)).scalar() or 0

        result = await db.execute(
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
            .order_by(VitalSign.recorded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_latest(
        db: AsyncSession, patient_id: uuid.UUID
    ) -> VitalSign | None:
        result = await db.execute(
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
            .order_by(VitalSign.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_trend(
        db: AsyncSession,
        patient_id: uuid.UUID,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Sequence[VitalSign]:
        """Get vital signs trend for a patient."""
        q = (
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
            .order_by(VitalSign.recorded_at.asc())
        )
        if start_date:
            q = q.where(VitalSign.recorded_at >= start_date)
        if end_date:
            q = q.where(VitalSign.recorded_at <= end_date)
        result = await db.execute(q)
        return list(result.scalars().all())
