from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.visit import Visit
from app.models.visit_summary import VisitSummary
from app.schemas.visit import VisitReferralCreate
from app.services.audit import AuditService


class VisitService:
    """Visit lifecycle management with 5-state model."""

    VALID_TRANSITIONS: dict[str, list[str]] = {
        "scheduled": ["checked-in", "cancelled"],
        "checked-in": ["in-progress", "cancelled"],
        "in-progress": ["completed"],
        "completed": [],
        "cancelled": [],
    }

    VISIT_REASONS = [
        "consultation", "follow-up", "procedure",
        "emergency", "lab", "vaccination", "other",
    ]

    @staticmethod
    async def create_walkin_visit(
        db: AsyncSession,
        patient_id: uuid.UUID,
        department_id: uuid.UUID | None,
        reason: str,
        reason_notes: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> Visit:
        if reason not in VisitService.VISIT_REASONS:
            raise ValueError(f"Invalid reason: {reason}. Must be one of {VisitService.VISIT_REASONS}")

        now = datetime.now(timezone.utc)
        visit = Visit(
            patient_id=patient_id,
            department_id=department_id,
            reason=reason,
            reason_notes=reason_notes,
            status="scheduled",
            created_by=created_by or uuid.uuid4(),
        )
        db.add(visit)
        await db.flush()

        # Walk-ins auto check-in immediately (D-34)
        visit.status = "checked-in"
        visit.checked_in_at = now

        await AuditService.log_event(
            db,
            user_id=created_by,
            action="walkin_visit_created",
            resource="visit",
            resource_id=str(visit.id),
            patient_id=patient_id,
            metadata={"reason": reason, "department_id": str(department_id) if department_id else None},
        )
        await db.flush()
        return visit

    @staticmethod
    async def create_scheduled_visit(
        db: AsyncSession,
        patient_id: uuid.UUID,
        department_id: uuid.UUID | None,
        doctor_id: uuid.UUID | None,
        reason: str,
        scheduled_at: datetime,
        created_by: uuid.UUID,
        reason_notes: str | None = None,
    ) -> Visit:
        if reason not in VisitService.VISIT_REASONS:
            raise ValueError(f"Invalid reason: {reason}")

        visit = Visit(
            patient_id=patient_id,
            department_id=department_id,
            doctor_id=doctor_id,
            reason=reason,
            reason_notes=reason_notes,
            status="scheduled",
            scheduled_at=scheduled_at,
            created_by=created_by,
        )
        db.add(visit)

        await AuditService.log_event(
            db,
            user_id=created_by,
            action="scheduled_visit_created",
            resource="visit",
            resource_id=str(visit.id),
            patient_id=patient_id,
            metadata={"reason": reason, "scheduled_at": scheduled_at.isoformat()},
        )
        await db.flush()
        return visit

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        visit_id: uuid.UUID,
        new_status: str,
        changed_by: uuid.UUID,
        reason: str | None = None,
    ) -> Visit:
        result = await db.execute(select(Visit).where(Visit.id == visit_id))
        visit = result.scalar_one_or_none()
        if visit is None:
            raise ValueError("Visit not found")

        allowed = VisitService.VALID_TRANSITIONS.get(visit.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {visit.status} -> {new_status}. "
                f"Allowed: {allowed}"
            )

        now = datetime.now(timezone.utc)
        old_status = visit.status
        visit.status = new_status

        if new_status == "checked-in":
            visit.checked_in_at = now
        elif new_status == "in-progress":
            visit.started_at = now
        elif new_status == "completed":
            visit.completed_at = now
            # Auto-calculate duration (D-36)
            if visit.checked_in_at:
                delta = now - visit.checked_in_at
                visit.duration_minutes = int(delta.total_seconds() / 60)
            # Auto-generate summary (D-38)
            await VisitService._generate_summary(db, visit)
        elif new_status == "cancelled":
            visit.cancelled_at = now
            visit.cancellation_reason = reason

        await AuditService.log_event(
            db,
            user_id=changed_by,
            action="visit_status_transition",
            resource="visit",
            resource_id=str(visit.id),
            patient_id=visit.patient_id,
            metadata={"old_status": old_status, "new_status": new_status, "reason": reason},
        )
        await db.flush()
        return visit

    @staticmethod
    async def _generate_summary(db: AsyncSession, visit: Visit) -> VisitSummary:
        doctor_name = None
        if visit.doctor_id:
            result = await db.execute(select(User).where(User.id == visit.doctor_id))
            doctor = result.scalar_one_or_none()
            if doctor:
                doctor_name = f"{doctor.first_name} {doctor.last_name}"

        summary = VisitSummary(
            visit_id=visit.id,
            doctor_name=doctor_name,
            diagnosis=None,
            diagnoses=[],
            prescriptions=[],
            procedures_performed=[],
            lab_orders=[],
            notes=f"Visit reason: {visit.reason}",
        )
        db.add(summary)
        await db.flush()
        return summary

    @staticmethod
    async def get_visits_for_patient(
        db: AsyncSession,
        patient_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[Visit], int]:
        count_q = select(func.count()).select_from(Visit).where(Visit.patient_id == patient_id)
        total = (await db.execute(count_q)).scalar() or 0

        q = (
            select(Visit)
            .where(Visit.patient_id == patient_id)
            .order_by(Visit.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(q)
        visits = result.scalars().all()
        return visits, total

    @staticmethod
    async def get_visit(db: AsyncSession, visit_id: uuid.UUID) -> Visit | None:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Visit)
            .options(selectinload(Visit.summary))
            .where(Visit.id == visit_id)
        )
        return result.scalar_one_or_none()
