from fastapi import APIRouter

from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.break_glass import router as break_glass_router
from app.api.v1.password import router as password_router
from app.api.v1.rbac import router as rbac_router

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


router.include_router(auth_router)
router.include_router(password_router)
router.include_router(rbac_router)
router.include_router(audit_router)
router.include_router(break_glass_router)
