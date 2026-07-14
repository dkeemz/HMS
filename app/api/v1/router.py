from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.password import router as password_router

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


router.include_router(auth_router)
router.include_router(password_router)
