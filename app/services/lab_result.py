"""Lab Result service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_result import LabResult
from app.schemas.lab_result import LabResultCreate, LabResultUpdate
from app.services.audit import AuditService


class LabResultService:
    @staticmethod
    async def create_order(
        db: AsyncSession, data: LabResultCreate, ordered_by: uuid.UUID
    ) -> LabResult:
        lr = LabResult(
            visit_id=data.visit_id,
            patient_id=data.patient_id,
            ordered_by=ordered_by,
            test_name=data.test_name,
            category=data.category,
            clinical_question=data.clinical_question,
        )
        db.add(lr)
        await db.flush()
        await db.refresh(lr)
        await AuditService.log(
            db, "lab_result", lr.id, "create",
            detail=f"Lab order '{data.test_name}' created for visit {data.visit_id}",
        )
        return lr

    @staticmethod
    async def get(db: AsyncSession, lr_id: uuid.UUID) -> LabResult | None:
        result = await db.execute(
            select(LabResult).where(LabResult.id == lr_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_visit(
        db: AsyncSession, visit_id: uuid.UUID
    ) -> Sequence[LabResult]:
        result = await db.execute(
            select(LabResult)
            .where(LabResult.visit_id == visit_id)
            .order_by(LabResult.ordered_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_patient(
        db: AsyncSession, patient_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[LabResult], int]:
        count_q = select(func.count()).select_from(LabResult).where(
            LabResult.patient_id == patient_id
        )
        total = (await db.execute(count_q)).scalar() or 0

        result = await db.execute(
            select(LabResult)
            .where(LabResult.patient_id == patient_id)
            .order_by(LabResult.ordered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def update(
        db: AsyncSession, lr: LabResult, data: LabResultUpdate
    ) -> LabResult:
        update_data = data.model_dump(exclude_unset=True)

        # Auto-set completed_at when status changes to completed
        if update_data.get("status") == "completed" and lr.status != "completed":
            update_data["completed_at"] = datetime.now(timezone.utc)

        # Auto-set abnormal_flag based on reference range (if not explicitly set)
        if (
            "result_value" in update_data
            and "abnormal_flag" not in update_data
            and lr.reference_range
        ):
            update_data["abnormal_flag"] = LabResultService._compute_abnormal_flag(
                update_data["result_value"], lr.reference_range
            )

        for field, value in update_data.items():
            setattr(lr, field, value)

        await db.flush()
        await db.refresh(lr)
        return lr

    @staticmethod
    def _compute_abnormal_flag(value: str, reference_range: str) -> str:
        """Compute abnormal flag from result value and reference range."""
        try:
            # Parse reference range like "7.0-11.0" or "< 5.0"
            val = float(value.replace("<", "").replace(">", "").strip())
            if "-" in reference_range:
                parts = reference_range.split("-")
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                if val < low:
                    return "low" if val >= low * 0.7 else "critical_low"
                elif val > high:
                    return "high" if val <= high * 1.3 else "critical_high"
                return "normal"
            return "normal"
        except (ValueError, IndexError):
            return "normal"

    @staticmethod
    async def list_abnormal(
        db: AsyncSession, patient_id: uuid.UUID
    ) -> Sequence[LabResult]:
        """Get all abnormal results for a patient."""
        result = await db.execute(
            select(LabResult)
            .where(
                LabResult.patient_id == patient_id,
                LabResult.abnormal_flag != "normal",
            )
            .order_by(LabResult.ordered_at.desc())
        )
        return list(result.scalars().all())
