from fastapi import APIRouter

from app.api.v1.appointments import router as appointments_router
from app.api.v1.availability import router as availability_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.break_glass import router as break_glass_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.departments import router as departments_router
from app.api.v1.doctors import router as doctors_router
from app.api.v1.ehr import router as ehr_router
from app.api.v1.insurance import providers_router, router as insurance_router
from app.api.v1.medical_history import router as medical_history_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.patient_search import router as patient_search_router
from app.api.v1.password import router as password_router
from app.api.v1.patients import router as patients_router
from app.api.v1.rbac import router as rbac_router
from app.api.v1.visits import router as visits_router

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


router.include_router(auth_router)
router.include_router(password_router)
router.include_router(rbac_router)
router.include_router(audit_router)
router.include_router(appointments_router)
router.include_router(availability_router)
router.include_router(break_glass_router)
router.include_router(dashboard_router)
router.include_router(departments_router)
router.include_router(doctors_router)
router.include_router(ehr_router)
router.include_router(notifications_router)
router.include_router(patient_search_router)
router.include_router(patients_router)
router.include_router(medical_history_router)
router.include_router(insurance_router)
router.include_router(providers_router)
router.include_router(visits_router)
