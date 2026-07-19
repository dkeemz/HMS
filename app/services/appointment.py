"""Appointment service — CRUD, conflict detection, walk-in, reschedule, cancel."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment
from app.models.user import User
from app.schemas.appointment import (
    APPOINTMENT_TYPES,
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentUpdate,
    WalkInCreate,
)
from app.services.audit import AuditService


class AppointmentService:
    """Appointment lifecycle management."""

    VALID_TRANSITIONS: dict[str, list[str]] = {
        "scheduled": ["confirmed", "checked-in", "cancelled", "rescheduled", "no-show"],
        "confirmed": ["checked-in", "cancelled", "rescheduled", "no-show"],
        "checked-in": ["in-progress", "cancelled"],
        "in-progress": ["completed"],
        "completed": [],
        "cancelled": [],
        "no-show": ["scheduled"],
        "rescheduled": [],
    }

    @staticmethod
    def compute_end_at(scheduled_at: datetime, duration_minutes: int) -> datetime:
        return scheduled_at + timedelta(minutes=duration_minutes)

    @staticmethod
    async def check_conflict(
        db: AsyncSession,
        doctor_id: uuid.UUID,
        scheduled_at: datetime,
        duration_minutes: int,
        exclude_id: uuid.UUID | None = None,
    ) -> Appointment | None:
        """Return the conflicting appointment if double-booking, else None."""
        end_at = AppointmentService.compute_end_at(scheduled_at, duration_minutes)
        # Overlap: existing.start < new.end AND existing.end > new.start
        q = select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.status.notin_(["cancelled", "rescheduled"]),
                Appointment.scheduled_at < end_at,
                Appointment.end_at > scheduled_at,
            )
        )
        if exclude_id:
            q = q.where(Appointment.id != exclude_id)
        result = await db.execute(q)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_appointment(
        db: AsyncSession,
        data: AppointmentCreate,
        created_by: uuid.UUID,
    ) -> Appointment:
        """Create a new appointment with conflict check."""
        conflict = await AppointmentService.check_conflict(
            db, data.doctor_id, data.scheduled_at, data.duration_minutes,
        )
        if conflict:
            raise ValueError(
                f"Doctor already has an appointment at {conflict.scheduled_at:%Y-%m-%d %H:%M} "
                f"({conflict.appointment_type}, status: {conflict.status})"
            )

        end_at = AppointmentService.compute_end_at(data.scheduled_at, data.duration_minutes)
        appt = Appointment(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            department_id=data.department_id,
            appointment_type=data.appointment_type,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            end_at=end_at,
            priority=data.priority,
            room=data.room,
            notes=data.notes,
            created_by=created_by,
        )
        db.add(appt)
        await db.flush()
        await db.refresh(appt)

        await AuditService.log(
            db, "appointment", appt.id, "create",
            detail=f"Appointment created: {data.appointment_type} at {data.scheduled_at}",
        )
        return appt

    @staticmethod
    async def create_walkin(
        db: AsyncSession,
        data: WalkInCreate,
        created_by: uuid.UUID,
    ) -> Appointment:
        """Create a walk-in appointment — auto-schedule for now, assign queue position."""
        now = datetime.now(timezone.utc)
        duration = APPOINTMENT_TYPES.get(data.appointment_type, 15)

        # Get next queue position for today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.coalesce(func.max(Appointment.queue_position), 0)).where(
                and_(
                    Appointment.scheduled_at >= today_start,
                    Appointment.queue_position.isnot(None),
                )
            )
        )
        max_pos = result.scalar() or 0

        end_at = AppointmentService.compute_end_at(now, duration)
        appt = Appointment(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id or created_by,
            department_id=data.department_id,
            appointment_type=data.appointment_type,
            scheduled_at=now,
            duration_minutes=duration,
            end_at=end_at,
            status="checked-in",
            priority=data.priority,
            notes=data.notes,
            queue_position=max_pos + 1,
            checked_in_at=now,
            created_by=created_by,
        )
        db.add(appt)
        await db.flush()
        await db.refresh(appt)

        await AuditService.log(
            db, "appointment", appt.id, "create",
            detail=f"Walk-in created: queue #{appt.queue_position}",
        )
        return appt

    @staticmethod
    async def get_appointment(
        db: AsyncSession,
        appointment_id: uuid.UUID,
    ) -> Appointment | None:
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_appointments(
        db: AsyncSession,
        *,
        patient_id: uuid.UUID | None = None,
        doctor_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Appointment], int]:
        """List appointments with filters."""
        q = select(Appointment)
        count_q = select(func.count(Appointment.id))

        filters = []
        if patient_id:
            filters.append(Appointment.patient_id == patient_id)
        if doctor_id:
            filters.append(Appointment.doctor_id == doctor_id)
        if department_id:
            filters.append(Appointment.department_id == department_id)
        if status:
            filters.append(Appointment.status == status)
        if date_from:
            filters.append(Appointment.scheduled_at >= date_from)
        if date_to:
            filters.append(Appointment.scheduled_at <= date_to)

        if filters:
            q = q.where(and_(*filters))
            count_q = count_q.where(and_(*filters))

        total_result = await db.execute(count_q)
        total = total_result.scalar() or 0

        q = q.order_by(Appointment.scheduled_at.desc()).offset(offset).limit(limit)
        result = await db.execute(q)
        return result.scalars().all(), total

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        appointment_id: uuid.UUID,
        new_status: str,
    ) -> Appointment:
        appt = await AppointmentService.get_appointment(db, appointment_id)
        if not appt:
            raise ValueError("Appointment not found")

        valid = AppointmentService.VALID_TRANSITIONS.get(appt.status, [])
        if new_status not in valid:
            raise ValueError(
                f"Cannot transition from '{appt.status}' to '{new_status}'. "
                f"Valid transitions: {valid}"
            )

        appt.status = new_status
        now = datetime.now(timezone.utc)
        if new_status == "checked-in":
            appt.checked_in_at = now
        elif new_status == "completed":
            appt.completed_at = now
        elif new_status == "cancelled":
            appt.cancelled_at = now

        await db.flush()
        await db.refresh(appt)
        await AuditService.log(
            db, "appointment", appt.id, "update",
            detail=f"Status: {appt.status} -> {new_status}",
        )
        return appt

    @staticmethod
    async def reschedule(
        db: AsyncSession,
        appointment_id: uuid.UUID,
        data: AppointmentReschedule,
    ) -> Appointment:
        appt = await AppointmentService.get_appointment(db, appointment_id)
        if not appt:
            raise ValueError("Appointment not found")
        if appt.status in ("completed", "cancelled"):
            raise ValueError(f"Cannot reschedule a {appt.status} appointment")

        conflict = await AppointmentService.check_conflict(
            db, appt.doctor_id, data.new_scheduled_at, appt.duration_minutes,
            exclude_id=appointment_id,
        )
        if conflict:
            raise ValueError(
                f"Doctor already has an appointment at {conflict.scheduled_at}"
            )

        appt.status = "rescheduled"
        appt.rescheduled_from = appointment_id
        appt.cancelled_at = datetime.now(timezone.utc)

        end_at = AppointmentService.compute_end_at(data.new_scheduled_at, appt.duration_minutes)
        new_appt = Appointment(
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id,
            department_id=appt.department_id,
            appointment_type=appt.appointment_type,
            scheduled_at=data.new_scheduled_at,
            duration_minutes=appt.duration_minutes,
            end_at=end_at,
            status="scheduled",
            priority=appt.priority,
            room=appt.room,
            notes=data.reason or appt.notes,
            rescheduled_from=appointment_id,
            created_by=appt.created_by,
        )
        db.add(new_appt)
        await db.flush()
        await db.refresh(new_appt)

        await AuditService.log(
            db, "appointment", appt.id, "update",
            detail=f"Rescheduled to {data.new_scheduled_at}",
        )
        return new_appt

    @staticmethod
    async def cancel(
        db: AsyncSession,
        appointment_id: uuid.UUID,
        data: AppointmentCancel,
    ) -> Appointment:
        appt = await AppointmentService.get_appointment(db, appointment_id)
        if not appt:
            raise ValueError("Appointment not found")
        if appt.status in ("completed", "cancelled"):
            raise ValueError(f"Cannot cancel a {appt.status} appointment")

        appt.status = "cancelled"
        appt.cancellation_reason = data.reason
        appt.cancelled_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(appt)

        await AuditService.log(
            db, "appointment", appt.id, "update",
            detail=f"Cancelled: {data.reason}",
        )
        return appt

    @staticmethod
    async def get_queue(
        db: AsyncSession,
        department_id: uuid.UUID | None = None,
    ) -> list[Appointment]:
        """Get current day queue — checked-in and in-progress appointments."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        q = select(Appointment).where(
            and_(
                Appointment.scheduled_at >= today_start,
                Appointment.status.in_(["checked-in", "in-progress"]),
            )
        )
        if department_id:
            q = q.where(Appointment.department_id == department_id)
        q = q.order_by(Appointment.queue_position.asc())
        result = await db.execute(q)
        return list(result.scalars().all())
