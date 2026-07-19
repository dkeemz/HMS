"""Appointments API — REST + HTMX endpoints."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.user import User
from app.middleware.permission import require_permission
from app.schemas.appointment import (
    APPOINTMENT_TYPES,
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentUpdate,
    WalkInCreate,
)
from app.services.appointment import AppointmentService
from app.services.audit import AuditService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _get_template(name: str):
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
    return env.get_template(name)


def _user_ctx(user) -> dict:
    return {
        "user_full_name": f"{user.first_name} {user.last_name}",
        "user_email": user.email,
        "user_initials": (user.first_name[0] + user.last_name[0]).upper(),
    }


# ── REST API ─────────────────────────────────────────────────────────────

@router.get("/")
async def list_appointments(
    patient_id: uuid.UUID | None = None,
    doctor_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "read")),
):
    appts, total = await AppointmentService.list_appointments(
        db, patient_id=patient_id, doctor_id=doctor_id,
        department_id=department_id, status=status_filter,
        date_from=date_from, date_to=date_to,
        limit=limit, offset=offset,
    )
    return {"items": [str(a.id) for a in appts], "total": total}


@router.post("/")
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "create")),
):
    try:
        appt = await AppointmentService.create_appointment(db, data, current_user.id)
        await db.commit()
        return {"id": str(appt.id), "status": appt.status, "message": "Appointment created"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "read")),
):
    appt = await AppointmentService.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {
        "id": str(appt.id),
        "patient_id": str(appt.patient_id),
        "doctor_id": str(appt.doctor_id),
        "department_id": str(appt.department_id) if appt.department_id else None,
        "appointment_type": appt.appointment_type,
        "scheduled_at": appt.scheduled_at.isoformat(),
        "duration_minutes": appt.duration_minutes,
        "end_at": appt.end_at.isoformat(),
        "status": appt.status,
        "priority": appt.priority,
        "room": appt.room,
        "notes": appt.notes,
        "queue_position": appt.queue_position,
    }


@router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "update")),
):
    appt = await AppointmentService.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    update_data = data.model_dump(exclude_unset=True)
    if "scheduled_at" in update_data and "duration_minutes" not in update_data:
        update_data["duration_minutes"] = appt.duration_minutes
    for key, val in update_data.items():
        setattr(appt, key, val)
    if "scheduled_at" in update_data or "duration_minutes" in update_data:
        appt.end_at = AppointmentService.compute_end_at(appt.scheduled_at, appt.duration_minutes)
    await db.flush()
    await db.refresh(appt)
    return {"id": str(appt.id), "status": appt.status}


@router.post("/{appointment_id}/check-in")
async def check_in(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "update")),
):
    try:
        appt = await AppointmentService.transition_status(db, appointment_id, "checked-in")
        await db.commit()
        return {"id": str(appt.id), "status": appt.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/start")
async def start_consultation(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "update")),
):
    try:
        appt = await AppointmentService.transition_status(db, appointment_id, "in-progress")
        await db.commit()
        return {"id": str(appt.id), "status": appt.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "update")),
):
    try:
        appt = await AppointmentService.transition_status(db, appointment_id, "completed")
        await db.commit()
        return {"id": str(appt.id), "status": appt.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentReschedule,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "update")),
):
    try:
        new_appt = await AppointmentService.reschedule(db, appointment_id, data)
        await db.commit()
        return {"id": str(new_appt.id), "status": new_appt.status, "message": "Rescheduled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "update")),
):
    try:
        appt = await AppointmentService.cancel(db, appointment_id, data)
        await db.commit()
        return {"id": str(appt.id), "status": appt.status, "message": "Cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Walk-in / Queue ──────────────────────────────────────────────────────

@router.post("/walk-in")
async def create_walkin(
    data: WalkInCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "create")),
):
    try:
        appt = await AppointmentService.create_walkin(db, data, current_user.id)
        await db.commit()
        return {
            "id": str(appt.id),
            "queue_position": appt.queue_position,
            "status": appt.status,
            "message": f"Walk-in registered — queue #{appt.queue_position}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/queue/list")
async def get_queue(
    department_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "read")),
):
    queue = await AppointmentService.get_queue(db, department_id)
    return [
        {
            "id": str(a.id),
            "patient_id": str(a.patient_id),
            "position": a.queue_position,
            "priority": a.priority,
            "type": a.appointment_type,
            "status": a.status,
            "checked_in_at": a.checked_in_at.isoformat() if a.checked_in_at else None,
        }
        for a in queue
    ]


# ── HTMX Page Fragments ─────────────────────────────────────────────────

@router.get("/page/list", response_class=HTMLResponse)
async def appointments_page(
    request: Request,
    status_filter: str | None = Query(None, alias="status"),
    doctor_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "read")),
):
    appts, total = await AppointmentService.list_appointments(
        db, doctor_id=doctor_id, status=status_filter, limit=50,
    )
    tmpl = _get_template("appointments/list.html")
    html = tmpl.render(
        request=request,
        appointments=appts,
        total=total,
        status_filter=status_filter or "",
        appointment_types=APPOINTMENT_TYPES,
        **_user_ctx(current_user),
    )
    return HTMLResponse(content=html)


@router.get("/page/queue", response_class=HTMLResponse)
async def queue_page(
    request: Request,
    department_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "read")),
):
    queue = await AppointmentService.get_queue(db, department_id)
    tmpl = _get_template("appointments/queue.html")
    html = tmpl.render(
        request=request,
        queue=queue,
        **_user_ctx(current_user),
    )
    return HTMLResponse(content=html)


@router.post("/page/book", response_class=HTMLResponse)
async def book_appointment_form(
    request: Request,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    scheduled_at: datetime,
    appointment_type: str = "consultation",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointment", "create")),
):
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_at=scheduled_at,
        appointment_type=appointment_type,
    )
    try:
        appt = await AppointmentService.create_appointment(db, data, current_user.id)
        await db.commit()
        return HTMLResponse(
            content=f'<div class="alert alert-success">Appointment booked at {appt.scheduled_at:%H:%M}</div>'
        )
    except ValueError as e:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{e}</div>',
            status_code=409,
        )
