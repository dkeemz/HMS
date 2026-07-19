"""Availability API — slot queries for doctors."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.user import User
from app.middleware.permission import require_permission
from app.services.availability import AvailabilityService

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("/{doctor_id}/slots")
async def get_doctor_slots(
    doctor_id: uuid.UUID,
    date_str: str = Query(..., alias="date"),
    duration_minutes: int = 15,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "read")),
):
    """Get available time slots for a doctor on a specific date."""
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    slots = await AvailabilityService.get_available_slots(
        db, doctor_id, target_date, duration_minutes,
    )
    return {
        "doctor_id": str(doctor_id),
        "date": date_str,
        "slots": [
            {
                "start": s.start.isoformat(),
                "end": s.end.isoformat(),
                "available": s.available,
                "reason": s.reason,
            }
            for s in slots
        ],
    }


@router.get("/{doctor_id}/summary")
async def get_doctor_summary(
    doctor_id: uuid.UUID,
    date_str: str = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "read")),
):
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    return await AvailabilityService.get_doctor_availability_summary(
        db, doctor_id, target_date,
    )
