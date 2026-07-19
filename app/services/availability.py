"""Availability service — compute available slots from doctor profiles + bookings."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone, time
from typing import Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.doctor_profile import DoctorProfile
from app.schemas.appointment import TimeSlot


class AvailabilityService:
    """Compute available time slots for a doctor on a given date."""

    DEFAULT_WORK_START = time(8, 0)
    DEFAULT_WORK_END = time(17, 0)
    DEFAULT_SLOT_MINUTES = 15
    BREAK_START = time(12, 0)
    BREAK_END = time(13, 0)

    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        doctor_id: uuid.UUID,
        target_date: date,
        duration_minutes: int = 15,
    ) -> list[TimeSlot]:
        """Generate available time slots for a doctor on a specific date."""
        # Get doctor profile for working hours
        result = await db.execute(
            select(DoctorProfile).where(DoctorProfile.user_id == doctor_id)
        )
        profile = result.scalar_one_or_none()

        if not profile or not profile.is_accepting_patients:
            return []
        if profile.availability_status in ("on-leave", "unavailable"):
            return []

        # Parse consultation hours or use defaults
        work_start, work_end = AvailabilityService._get_work_hours(profile, target_date)
        if not work_start or not work_end:
            return []

        # Get existing appointments for this doctor on this date
        day_start = datetime.combine(target_date, time(0, 0), tzinfo=timezone.utc)
        day_end = datetime.combine(target_date + timedelta(days=1), time(0, 0), tzinfo=timezone.utc)

        existing_result = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.doctor_id == doctor_id,
                    Appointment.scheduled_at >= day_start,
                    Appointment.scheduled_at < day_end,
                    Appointment.status.notin_(["cancelled", "rescheduled"]),
                )
            )
        )
        existing = list(existing_result.scalars().all())

        # Generate all possible slots
        slots = []
        current = datetime.combine(target_date, work_start, tzinfo=timezone.utc)
        work_end_dt = datetime.combine(target_date, work_end, tzinfo=timezone.utc)

        while current + timedelta(minutes=duration_minutes) <= work_end_dt:
            slot_end = current + timedelta(minutes=duration_minutes)

            # Skip lunch break
            break_start = datetime.combine(target_date, AvailabilityService.BREAK_START, tzinfo=timezone.utc)
            break_end = datetime.combine(target_date, AvailabilityService.BREAK_END, tzinfo=timezone.utc)
            if current < break_end and slot_end > break_start:
                current = break_end
                continue

            # Check if slot conflicts with existing appointments
            available = True
            reason = None
            for appt in existing:
                if appt.scheduled_at < slot_end and appt.end_at > current:
                    available = False
                    reason = f"Booked ({appt.appointment_type})"
                    break

            slots.append(TimeSlot(
                start=current,
                end=slot_end,
                available=available,
                doctor_id=doctor_id,
                reason=reason,
            ))

            current = slot_end

        return slots

    @staticmethod
    def _get_work_hours(
        profile: DoctorProfile,
        target_date: date,
    ) -> tuple[time | None, time | None]:
        """Parse consultation_hours JSONB to get work hours for the day of week."""
        hours = profile.consultation_hours
        if not hours:
            return AvailabilityService.DEFAULT_WORK_START, AvailabilityService.DEFAULT_WORK_END

        day_name = target_date.strftime("%A").lower()
        if isinstance(hours, dict):
            day_hours = hours.get(day_name) or hours.get("default")
            if day_hours and isinstance(day_hours, dict):
                start_str = day_hours.get("start", "08:00")
                end_str = day_hours.get("end", "17:00")
                try:
                    sh, sm = map(int, start_str.split(":"))
                    eh, em = map(int, end_str.split(":"))
                    return time(sh, sm), time(eh, em)
                except (ValueError, AttributeError):
                    pass
            elif day_hours is None:
                return None, None

        return AvailabilityService.DEFAULT_WORK_START, AvailabilityService.DEFAULT_WORK_END

    @staticmethod
    async def get_doctor_availability_summary(
        db: AsyncSession,
        doctor_id: uuid.UUID,
        target_date: date,
    ) -> dict:
        """Get a summary of availability: total slots, available, booked."""
        slots = await AvailabilityService.get_available_slots(db, doctor_id, target_date)
        total = len(slots)
        available = sum(1 for s in slots if s.available)
        booked = total - available
        return {
            "doctor_id": str(doctor_id),
            "date": target_date.isoformat(),
            "total_slots": total,
            "available_slots": available,
            "booked_slots": booked,
        }
