from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.schemas.doctor import (
    AvailabilityUpdate,
    DoctorProfileCreate,
    DoctorProfileResponse,
    DoctorProfileUpdate,
)
from app.services.doctor import DoctorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doctors", tags=["doctors"])

_jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=True,
)


def _render(template_name: str, context: dict | None = None) -> str:
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(context or {})


# ── JSON API endpoints ──────────────────────────────────────────────────────


@router.post("/profiles", response_model=DoctorProfileResponse, status_code=201)
async def create_doctor_profile(
    body: DoctorProfileCreate,
    current_user = Depends(require_permission("doctor", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Create a doctor profile linked to an existing user."""
    try:
        profile = await DoctorService.create_profile(db, body, current_user.id)
        await db.commit()
        return DoctorProfileResponse.model_validate(profile)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=list[DoctorProfileResponse])
async def list_doctors(
    department_id: uuid.UUID | None = Query(None),
    specialty: str | None = Query(None),
    is_accepting: bool | None = Query(None),
    availability_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user = Depends(require_permission("doctor", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List doctor profiles with filters and pagination."""
    doctors, _total = await DoctorService.list_doctors(
        db,
        department_id=department_id,
        specialty=specialty,
        is_accepting=is_accepting,
        availability_status=availability_status,
        page=page,
        page_size=page_size,
    )
    return [DoctorProfileResponse.model_validate(d) for d in doctors]


@router.get("/search")
async def search_doctors(
    q: str = Query(..., min_length=1),
    department_id: uuid.UUID | None = Query(None),
    specialty: str | None = Query(None),
    current_user = Depends(require_permission("doctor", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Search doctors by name, specialty, or department."""
    doctors = await DoctorService.search_doctors(
        db, q=q, department_id=department_id, specialty=specialty
    )
    return [DoctorProfileResponse.model_validate(d) for d in doctors]


@router.get("/list-rows", response_class=HTMLResponse)
async def list_doctor_rows_html(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department_id: uuid.UUID | None = Query(None),
    specialty: str | None = Query(None),
    availability_status: str | None = Query(None),
    current_user = Depends(require_permission("doctor", "read")),
    db: AsyncSession = Depends(get_db),
):
    """HTMX fragment: doctor list table rows."""
    doctors, total = await DoctorService.list_doctors(
        db,
        department_id=department_id,
        specialty=specialty,
        availability_status=availability_status,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    html = _render("components/doctor_list_rows.html", {
        "doctors": doctors,
        "page": page,
        "total": total,
        "total_pages": total_pages,
    })
    return HTMLResponse(html)


@router.get("/{user_id}", response_model=DoctorProfileResponse)
async def get_doctor_profile(
    user_id: str,
    current_user = Depends(require_permission("doctor", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single doctor profile by user_id."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    profile = await DoctorService.get_profile(db, uid)
    if profile is None:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return DoctorProfileResponse.model_validate(profile)


@router.put("/{user_id}", response_model=DoctorProfileResponse)
async def update_doctor_profile(
    user_id: str,
    body: DoctorProfileUpdate,
    current_user = Depends(require_permission("doctor", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a doctor profile."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    try:
        profile = await DoctorService.update_profile(db, uid, body, current_user.id)
        await db.commit()
        return DoctorProfileResponse.model_validate(profile)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}/availability", response_model=DoctorProfileResponse)
async def update_availability(
    user_id: str,
    body: AvailabilityUpdate,
    current_user = Depends(require_permission("doctor", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Toggle doctor availability status."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    try:
        profile = await DoctorService.update_availability(
            db, uid, body.availability_status, current_user.id
        )
        await db.commit()
        return DoctorProfileResponse.model_validate(profile)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
