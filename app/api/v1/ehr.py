"""EHR API — Clinical notes, vitals, diagnoses, lab results, documents."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.user import User
from app.middleware.permission import require_permission
from app.schemas.clinical_document import ClinicalDocumentCreate
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisUpdate
from app.schemas.ehr_note import EhrNoteCreate, EhrNoteUpdate
from app.schemas.lab_result import LabResultCreate, LabResultUpdate
from app.schemas.vital_signs import VitalSignCreate
from app.services.clinical_document import ClinicalDocumentService
from app.services.diagnosis import DiagnosisService
from app.services.ehr_note import EhrNoteService
from app.services.lab_result import LabResultService
from app.services.vital_signs import VitalSignService

router = APIRouter(prefix="/ehr", tags=["EHR"])


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


# ── Clinical Notes (SOAP) ────────────────────────────────────────────────

@router.post("/notes", status_code=status.HTTP_201_CREATED)
async def create_note(
    data: EhrNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "create")),
):
    note = await EhrNoteService.create(db, data, current_user.id)
    await db.commit()
    return {"id": str(note.id), "status": note.status, "message": "Note created"}


@router.get("/notes/{note_id}")
async def get_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    note = await EhrNoteService.get(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": str(note.id),
        "visit_id": str(note.visit_id),
        "patient_id": str(note.patient_id),
        "doctor_id": str(note.doctor_id) if note.doctor_id else None,
        "subjective": note.subjective,
        "objective": note.objective,
        "assessment": note.assessment,
        "plan": note.plan,
        "note_type": note.note_type,
        "status": note.status,
        "signed_at": note.signed_at.isoformat() if note.signed_at else None,
        "created_at": note.created_at.isoformat(),
    }


@router.get("/visits/{visit_id}/notes")
async def list_notes_by_visit(
    visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    notes = await EhrNoteService.list_by_visit(db, visit_id)
    return {"items": [
        {
            "id": str(n.id), "note_type": n.note_type, "status": n.status,
            "doctor_id": str(n.doctor_id) if n.doctor_id else None,
            "created_at": n.created_at.isoformat(),
            "signed_at": n.signed_at.isoformat() if n.signed_at else None,
        }
        for n in notes
    ], "total": len(notes)}


@router.get("/patients/{patient_id}/notes")
async def list_notes_by_patient(
    patient_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    notes, total = await EhrNoteService.list_by_patient(db, patient_id, limit, offset)
    return {"items": [
        {
            "id": str(n.id), "visit_id": str(n.visit_id),
            "note_type": n.note_type, "status": n.status,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ], "total": total}


@router.put("/notes/{note_id}")
async def update_note(
    note_id: uuid.UUID,
    data: EhrNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "update")),
):
    note = await EhrNoteService.get(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    try:
        note = await EhrNoteService.update(db, note, data)
        await db.commit()
        return {"id": str(note.id), "status": note.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notes/{note_id}/sign")
async def sign_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "update")),
):
    try:
        note = await EhrNoteService.sign(db, note_id)
        await db.commit()
        return {"id": str(note.id), "status": "signed", "signed_at": note.signed_at.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Vital Signs ───────────────────────────────────────────────────────────

@router.post("/vitals", status_code=status.HTTP_201_CREATED)
async def record_vitals(
    data: VitalSignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "create")),
):
    vs = await VitalSignService.record(db, data, current_user.id)
    await db.commit()
    return {"id": str(vs.id), "message": "Vitals recorded"}


@router.get("/vitals/{vital_id}")
async def get_vitals(
    vital_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    vs = await VitalSignService.get(db, vital_id)
    if not vs:
        raise HTTPException(status_code=404, detail="Vital sign record not found")
    return {
        "id": str(vs.id), "visit_id": str(vs.visit_id),
        "patient_id": str(vs.patient_id),
        "systolic_bp": vs.systolic_bp, "diastolic_bp": vs.diastolic_bp,
        "heart_rate": vs.heart_rate, "respiratory_rate": vs.respiratory_rate,
        "temperature": float(vs.temperature) if vs.temperature else None,
        "weight_kg": float(vs.weight_kg) if vs.weight_kg else None,
        "height_cm": float(vs.height_cm) if vs.height_cm else None,
        "spo2": vs.spo2, "pain_level": vs.pain_level,
        "bmi": vs.bmi,
        "recorded_at": vs.recorded_at.isoformat(),
    }


@router.get("/visits/{visit_id}/vitals")
async def list_vitals_by_visit(
    visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    vitals = await VitalSignService.list_by_visit(db, visit_id)
    return {"items": [
        {
            "id": str(v.id), "systolic_bp": v.systolic_bp, "diastolic_bp": v.diastolic_bp,
            "heart_rate": v.heart_rate, "temperature": float(v.temperature) if v.temperature else None,
            "recorded_at": v.recorded_at.isoformat(),
        }
        for v in vitals
    ], "total": len(vitals)}


@router.get("/patients/{patient_id}/vitals")
async def list_vitals_by_patient(
    patient_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    vitals, total = await VitalSignService.list_by_patient(db, patient_id, limit, offset)
    return {"items": [
        {
            "id": str(v.id), "visit_id": str(v.visit_id),
            "systolic_bp": v.systolic_bp, "diastolic_bp": v.diastolic_bp,
            "heart_rate": v.heart_rate, "temperature": float(v.temperature) if v.temperature else None,
            "recorded_at": v.recorded_at.isoformat(),
        }
        for v in vitals
    ], "total": total}


@router.get("/patients/{patient_id}/vitals/latest")
async def get_latest_vitals(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    vs = await VitalSignService.get_latest(db, patient_id)
    if not vs:
        return {"message": "No vitals recorded"}
    return {
        "id": str(vs.id), "systolic_bp": vs.systolic_bp,
        "diastolic_bp": vs.diastolic_bp, "heart_rate": vs.heart_rate,
        "respiratory_rate": vs.respiratory_rate,
        "temperature": float(vs.temperature) if vs.temperature else None,
        "weight_kg": float(vs.weight_kg) if vs.weight_kg else None,
        "height_cm": float(vs.height_cm) if vs.height_cm else None,
        "spo2": vs.spo2, "pain_level": vs.pain_level, "bmi": vs.bmi,
        "recorded_at": vs.recorded_at.isoformat(),
    }


@router.get("/patients/{patient_id}/vitals/trend")
async def get_vitals_trend(
    patient_id: uuid.UUID,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    vitals = await VitalSignService.get_trend(db, patient_id, start_date, end_date)
    return {"items": [
        {
            "id": str(v.id),
            "systolic_bp": v.systolic_bp, "diastolic_bp": v.diastolic_bp,
            "heart_rate": v.heart_rate, "temperature": float(v.temperature) if v.temperature else None,
            "weight_kg": float(v.weight_kg) if v.weight_kg else None,
            "spo2": v.spo2, "recorded_at": v.recorded_at.isoformat(),
        }
        for v in vitals
    ], "total": len(vitals)}


# ── Diagnoses ─────────────────────────────────────────────────────────────

@router.post("/diagnoses", status_code=status.HTTP_201_CREATED)
async def create_diagnosis(
    data: DiagnosisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "create")),
):
    dx = await DiagnosisService.create(db, data, current_user.id)
    await db.commit()
    return {"id": str(dx.id), "icd_code": dx.icd_code, "message": "Diagnosis recorded"}


@router.get("/diagnoses/{diagnosis_id}")
async def get_diagnosis(
    diagnosis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    dx = await DiagnosisService.get(db, diagnosis_id)
    if not dx:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return {
        "id": str(dx.id), "visit_id": str(dx.visit_id),
        "patient_id": str(dx.patient_id),
        "icd_code": dx.icd_code, "icd_version": dx.icd_version,
        "description": dx.description, "diagnosis_type": dx.diagnosis_type,
        "status": dx.status, "onset_date": str(dx.onset_date) if dx.onset_date else None,
        "resolved_date": str(dx.resolved_date) if dx.resolved_date else None,
        "created_at": dx.created_at.isoformat(),
    }


@router.get("/visits/{visit_id}/diagnoses")
async def list_diagnoses_by_visit(
    visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    dxs = await DiagnosisService.list_by_visit(db, visit_id)
    return {"items": [
        {
            "id": str(d.id), "icd_code": d.icd_code, "description": d.description,
            "diagnosis_type": d.diagnosis_type, "status": d.status,
        }
        for d in dxs
    ], "total": len(dxs)}


@router.get("/patients/{patient_id}/diagnoses")
async def list_diagnoses_by_patient(
    patient_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    dxs, total = await DiagnosisService.list_by_patient(db, patient_id, limit, offset)
    return {"items": [
        {
            "id": str(d.id), "visit_id": str(d.visit_id),
            "icd_code": d.icd_code, "description": d.description,
            "diagnosis_type": d.diagnosis_type, "status": d.status,
            "created_at": d.created_at.isoformat(),
        }
        for d in dxs
    ], "total": total}


@router.put("/diagnoses/{diagnosis_id}")
async def update_diagnosis(
    diagnosis_id: uuid.UUID,
    data: DiagnosisUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "update")),
):
    dx = await DiagnosisService.get(db, diagnosis_id)
    if not dx:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    dx = await DiagnosisService.update(db, dx, data)
    await db.commit()
    return {"id": str(dx.id), "status": dx.status}


@router.get("/icd/search")
async def search_icd_codes(
    q: str = Query(..., min_length=1),
    version: str = "10",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    results = await DiagnosisService.search_icd(db, q, version)
    # Deduplicate by icd_code
    seen = set()
    unique = []
    for r in results:
        if r.icd_code not in seen:
            seen.add(r.icd_code)
            unique.append({"code": r.icd_code, "description": r.description})
    return {"items": unique}


# ── Lab Results ───────────────────────────────────────────────────────────

@router.post("/labs", status_code=status.HTTP_201_CREATED)
async def order_lab(
    data: LabResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("lab_order", "create")),
):
    lr = await LabResultService.create_order(db, data, current_user.id)
    await db.commit()
    return {"id": str(lr.id), "status": lr.status, "message": "Lab ordered"}


@router.get("/labs/{lab_id}")
async def get_lab_result(
    lab_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("lab_result", "read")),
):
    lr = await LabResultService.get(db, lab_id)
    if not lr:
        raise HTTPException(status_code=404, detail="Lab result not found")
    return {
        "id": str(lr.id), "visit_id": str(lr.visit_id),
        "patient_id": str(lr.patient_id),
        "test_name": lr.test_name, "category": lr.category,
        "result_value": lr.result_value, "result_unit": lr.result_unit,
        "reference_range": lr.reference_range, "abnormal_flag": lr.abnormal_flag,
        "status": lr.status, "ordered_at": lr.ordered_at.isoformat(),
        "completed_at": lr.completed_at.isoformat() if lr.completed_at else None,
    }


@router.get("/visits/{visit_id}/labs")
async def list_labs_by_visit(
    visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("lab_result", "read")),
):
    labs = await LabResultService.list_by_visit(db, visit_id)
    return {"items": [
        {
            "id": str(l.id), "test_name": l.test_name, "category": l.category,
            "result_value": l.result_value, "abnormal_flag": l.abnormal_flag,
            "status": l.status,
        }
        for l in labs
    ], "total": len(labs)}


@router.get("/patients/{patient_id}/labs")
async def list_labs_by_patient(
    patient_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("lab_result", "read")),
):
    labs, total = await LabResultService.list_by_patient(db, patient_id, limit, offset)
    return {"items": [
        {
            "id": str(l.id), "visit_id": str(l.visit_id),
            "test_name": l.test_name, "category": l.category,
            "result_value": l.result_value, "abnormal_flag": l.abnormal_flag,
            "status": l.status, "ordered_at": l.ordered_at.isoformat(),
        }
        for l in labs
    ], "total": total}


@router.get("/patients/{patient_id}/labs/abnormal")
async def list_abnormal_labs(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("lab_result", "read")),
):
    labs = await LabResultService.list_abnormal(db, patient_id)
    return {"items": [
        {
            "id": str(l.id), "test_name": l.test_name,
            "result_value": l.result_value, "abnormal_flag": l.abnormal_flag,
            "ordered_at": l.ordered_at.isoformat(),
        }
        for l in labs
    ], "total": len(labs)}


@router.put("/labs/{lab_id}")
async def update_lab_result(
    lab_id: uuid.UUID,
    data: LabResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("lab_result", "update")),
):
    lr = await LabResultService.get(db, lab_id)
    if not lr:
        raise HTTPException(status_code=404, detail="Lab result not found")
    lr = await LabResultService.update(db, lr, data)
    await db.commit()
    return {"id": str(lr.id), "status": lr.status, "abnormal_flag": lr.abnormal_flag}


# ── Clinical Documents ────────────────────────────────────────────────────

@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    data: ClinicalDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "create")),
):
    doc = await ClinicalDocumentService.upload(db, data, current_user.id)
    await db.commit()
    return {"id": str(doc.id), "title": doc.title, "message": "Document uploaded"}


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    doc = await ClinicalDocumentService.get(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id), "patient_id": str(doc.patient_id),
        "visit_id": str(doc.visit_id) if doc.visit_id else None,
        "document_type": doc.document_type, "title": doc.title,
        "description": doc.description, "file_name": doc.file_name,
        "file_size": doc.file_size, "mime_type": doc.mime_type,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/patients/{patient_id}/documents")
async def list_documents_by_patient(
    patient_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    docs, total = await ClinicalDocumentService.list_by_patient(db, patient_id, limit, offset)
    return {"items": [
        {
            "id": str(d.id), "visit_id": str(d.visit_id) if d.visit_id else None,
            "document_type": d.document_type, "title": d.title,
            "file_name": d.file_name, "file_size": d.file_size,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ], "total": total}


# ── Patient Chart (aggregated view) ──────────────────────────────────────

@router.get("/patients/{patient_id}/chart")
async def get_patient_chart(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("medical_record", "read")),
):
    """Aggregate patient chart: latest vitals, active diagnoses, recent notes, abnormal labs."""
    latest_vitals = await VitalSignService.get_latest(db, patient_id)
    active_diagnoses, _ = await DiagnosisService.list_by_patient(db, patient_id, limit=100)
    recent_notes, notes_total = await EhrNoteService.list_by_patient(db, patient_id, limit=5)
    abnormal_labs = await LabResultService.list_abnormal(db, patient_id)

    return {
        "patient_id": patient_id,
        "latest_vitals": {
            "systolic_bp": latest_vitals.systolic_bp if latest_vitals else None,
            "diastolic_bp": latest_vitals.diastolic_bp if latest_vitals else None,
            "heart_rate": latest_vitals.heart_rate if latest_vitals else None,
            "temperature": float(latest_vitals.temperature) if latest_vitals and latest_vitals.temperature else None,
            "spo2": latest_vitals.spo2 if latest_vitals else None,
            "recorded_at": latest_vitals.recorded_at.isoformat() if latest_vitals else None,
        } if latest_vitals else None,
        "active_diagnoses": [
            {"id": str(d.id), "icd_code": d.icd_code, "description": d.description}
            for d in active_diagnoses if d.status == "active"
        ],
        "recent_notes": [
            {"id": str(n.id), "note_type": n.note_type, "status": n.status, "created_at": n.created_at.isoformat()}
            for n in recent_notes
        ],
        "abnormal_labs": [
            {"id": str(l.id), "test_name": l.test_name, "result_value": l.result_value, "abnormal_flag": l.abnormal_flag}
            for l in abnormal_labs
        ],
        "notes_total": notes_total,
    }
