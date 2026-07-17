from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.search import (
    PatientSearchParams,
    PatientSearchResponse,
    PatientSearchResult,
    TypeaheadResult,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class PatientSearchService:
    """Patient search using PostgreSQL pg_trgm (D-15). Audit-logged (D-68).

    Uses ilike for SQLite compatibility in tests; production PostgreSQL uses
    pg_trgm GIN indexes for fuzzy matching.
    """

    @staticmethod
    async def search_patients(
        db: AsyncSession,
        params: PatientSearchParams,
        user_id: uuid.UUID,
    ) -> PatientSearchResponse:
        """Search patients by name, MRN, phone with fuzzy matching.

        D-15: pg_trgm for fuzzy search (ilike fallback for SQLite)
        D-19: 4-character minimum (enforced by schema)
        D-20: 50 results per page
        D-68: Log every search with who, what query, when
        """
        query = params.q
        search_pattern = f"%{query}%"

        stmt = select(Patient).where(
            or_(
                Patient.mrn.ilike(search_pattern),
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.phone.ilike(search_pattern),
                Patient.email.ilike(search_pattern),
            )
        )

        if params.status:
            stmt = stmt.where(Patient.status == params.status)
        if params.gender:
            stmt = stmt.where(Patient.gender == params.gender)
        if params.date_from:
            stmt = stmt.where(Patient.date_of_birth >= params.date_from)
        if params.date_to:
            stmt = stmt.where(Patient.date_of_birth <= params.date_to)
        if params.state:
            stmt = stmt.where(Patient.address_state.ilike(f"%{params.state}%"))
        if params.city:
            stmt = stmt.where(Patient.address_city.ilike(f"%{params.city}%"))

        stmt = stmt.order_by(Patient.last_name, Patient.first_name)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        offset = (params.page - 1) * params.page_size
        result = await db.execute(stmt.offset(offset).limit(params.page_size))
        patients = list(result.scalars().all())

        await AuditService.log_event(
            db,
            user_id=user_id,
            action="patient_search",
            resource="patient",
            metadata={
                "query": query,
                "filters": {
                    "status": params.status,
                    "gender": params.gender,
                    "date_from": str(params.date_from) if params.date_from else None,
                    "date_to": str(params.date_to) if params.date_to else None,
                    "state": params.state,
                    "city": params.city,
                },
                "results_count": total,
                "page": params.page,
            },
            why="Patient search",
        )

        total_pages = max(1, (total + params.page_size - 1) // params.page_size)

        return PatientSearchResponse(
            results=[
                PatientSearchResult(
                    id=str(p.id),
                    mrn=p.mrn,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    date_of_birth=p.date_of_birth,
                    gender=p.gender,
                    phone=p.phone,
                    status=p.status,
                )
                for p in patients
            ],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    @staticmethod
    async def typeahead(
        db: AsyncSession,
        query: str,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> list[TypeaheadResult]:
        """Lightweight typeahead for HTMX autocomplete.

        Returns top results with minimal fields for fast response.
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(Patient)
            .where(
                or_(
                    Patient.mrn.ilike(search_pattern),
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern),
                )
            )
            .order_by(Patient.last_name, Patient.first_name)
            .limit(limit)
        )
        result = await db.execute(stmt)
        patients = list(result.scalars().all())

        await AuditService.log_event(
            db,
            user_id=user_id,
            action="patient_typeahead",
            resource="patient",
            metadata={"query": query, "results_count": len(patients)},
            why="Patient typeahead",
        )

        return [
            TypeaheadResult(
                id=str(p.id),
                mrn=p.mrn,
                first_name=p.first_name,
                last_name=p.last_name,
                status=p.status,
            )
            for p in patients
        ]
