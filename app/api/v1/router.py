from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


router.include_router(auth_router)
