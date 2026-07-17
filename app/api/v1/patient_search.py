from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.permission import require_permission
from app.models.user import User
from app.schemas.search import (
    PatientSearchResponse,
    TypeaheadResult,
)
from app.services.patient_search import PatientSearchService

router = APIRouter(prefix="/patients/search", tags=["Patient Search"])


@router.get("", response_model=PatientSearchResponse)
async def search_patients(
    q: str = Query(..., min_length=4, max_length=200, description="Search query (min 4 chars)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    status: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    date_from: str | None = Query(default=None, description="YYYY-MM-DD"),
    date_to: str | None = Query(default=None, description="YYYY-MM-DD"),
    state: str | None = Query(default=None),
    city: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
) -> PatientSearchResponse:
    """Unified patient search with advanced filters.

    D-15: pg_trgm fuzzy search (ilike on SQLite)
    D-17: Advanced filter panel (status, gender, DOB range, state, city)
    D-19: 4-character minimum query length
    D-20: 50 results per page with pagination
    D-68: Every search audit-logged
    """
    from datetime import date as _date

    params = {
        "q": q,
        "page": page,
        "page_size": page_size,
        "status": status,
        "gender": gender,
        "state": state,
        "city": city,
    }
    if date_from:
        params["date_from"] = _date.fromisoformat(date_from)
    if date_to:
        params["date_to"] = _date.fromisoformat(date_to)

    from app.schemas.search import PatientSearchParams

    search_params = PatientSearchParams(**params)
    return await PatientSearchService.search_patients(
        db, search_params, current_user.id
    )


@router.get("/typeahead", response_model=List[TypeaheadResult])
async def typeahead(
    q: str = Query(..., min_length=4, max_length=200, description="Search query (min 4 chars)"),
    limit: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("patient", "read")),
) -> List[TypeaheadResult]:
    """Lightweight typeahead for HTMX autocomplete.

    Returns top 10 results with id, mrn, name, status only.
    """
    return await PatientSearchService.typeahead(db, q, current_user.id, limit)
