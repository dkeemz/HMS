from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services.audit import AuditService
from app.services.patient import PatientService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])

_jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=True,
)


def _render(template_name: str, context: dict | None = None) -> str:
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(context or {})


# ── JSON API endpoints ──────────────────────────────────────────────────────


@router.post("/", response_model=PatientResponse, status_code=201)
async def register_patient(
    body: PatientCreate,
    current_user = Depends(require_permission("patient", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Register a new patient with demographics and auto-generated MRN."""
    try:
        patient = await PatientService.register_patient(db, body, current_user.id)
        await db.commit()
        return PatientResponse.model_validate(patient)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=list[PatientResponse])
async def list_patients(
    current_user = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 50,
):
    """List patients with pagination."""
    patients, _total = await PatientService.list_patients(
        db, page=page, page_size=page_size
    )
    return [PatientResponse.model_validate(p) for p in patients]


@router.get("/search", response_class=HTMLResponse)
async def search_patients_html(
    request: Request,
    q: str = "",
    current_user = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
):
    """HTMX fragment: patient search results as HTML cards."""
    if len(q.strip()) < 4:
        return HTMLResponse("<div class='empty-state'>Type at least 4 characters to search</div>")

    pattern = f"%{q.strip()}%"
    result = await db.execute(
        select(Patient)
        .options(selectinload(Patient.emergency_contacts), selectinload(Patient.next_of_kin))
        .where(
            or_(
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.mrn.ilike(pattern),
                Patient.phone.ilike(pattern),
            )
        )
        .order_by(Patient.created_at.desc())
        .limit(50)
    )
    patients = list(result.scalars().all())
    count = len(patients)

    await AuditService.log_event(
        db,
        user_id=current_user.id,
        action="patient_search",
        resource="patient",
        metadata={"query": q, "results_count": count},
        why="Patient search",
    )
    await db.flush()

    html = _render("components/patient_card.html", {"patients": patients})
    return HTMLResponse(html)


@router.get("/list", response_class=HTMLResponse)
async def list_patients_html(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    current_user = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
):
    """HTMX fragment: patient list table rows."""
    patients, total = await PatientService.list_patients(db, page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    html = _render("components/patient_list_rows.html", {
        "patients": patients,
        "page": page,
        "total": total,
        "total_pages": total_pages,
    })
    return HTMLResponse(html)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single patient by ID."""
    try:
        pid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = await PatientService.get_patient(db, pid)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}/detail", response_class=HTMLResponse)
async def patient_detail_html(
    patient_id: str,
    request: Request,
    current_user = Depends(require_permission("patient", "read")),
    db: AsyncSession = Depends(get_db),
):
    """HTMX fragment: patient detail panel for split view."""
    try:
        pid = uuid.UUID(patient_id)
    except ValueError:
        return HTMLResponse("<div class='empty-state'>Patient not found</div>")

    patient = await PatientService.get_patient(db, pid)
    if patient is None:
        return HTMLResponse("<div class='empty-state'>Patient not found</div>")

    html = _render("patients/profile_detail.html", {"patient": patient})
    return HTMLResponse(html)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    body: PatientUpdate,
    current_user = Depends(require_permission("patient", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update patient demographics."""
    try:
        pid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        patient = await PatientService.update_patient(
            db, pid, body, current_user.id
        )
        await db.commit()
        return PatientResponse.model_validate(patient)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
