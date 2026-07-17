"""Dashboard stats API — returns individual stat cards."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text

from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stat(
    stat: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Return a single stat value. Called by dashboard cards via HTMX."""
    if stat == "total_users":
        result = await db.execute(select(func.count(User.id)))
        count = result.scalar() or 0
        return {"value": str(count)}
    elif stat == "active_sessions":
        return {"value": "—"}
    elif stat == "recent_logins":
        return {"value": "—"}
    elif stat == "security_alerts":
        return {"value": "—"}
    return {"value": "—"}
