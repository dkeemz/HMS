"""Clinical Document service."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical_document import ClinicalDocument
from app.schemas.clinical_document import ClinicalDocumentCreate
from app.services.audit import AuditService


class ClinicalDocumentService:
    @staticmethod
    async def upload(
        db: AsyncSession, data: ClinicalDocumentCreate, uploaded_by: uuid.UUID
    ) -> ClinicalDocument:
        doc = ClinicalDocument(
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            uploaded_by=uploaded_by,
            document_type=data.document_type,
            title=data.title,
            description=data.description,
            file_name=data.file_name,
            file_path=data.file_path,
            file_size=data.file_size,
            mime_type=data.mime_type,
        )
        db.add(doc)
        await db.flush()
        await db.refresh(doc)
        await AuditService.log(
            db, "clinical_document", doc.id, "create",
            detail=f"Document '{data.title}' uploaded",
        )
        return doc

    @staticmethod
    async def get(db: AsyncSession, doc_id: uuid.UUID) -> ClinicalDocument | None:
        result = await db.execute(
            select(ClinicalDocument).where(ClinicalDocument.id == doc_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_patient(
        db: AsyncSession, patient_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[ClinicalDocument], int]:
        count_q = select(func.count()).select_from(ClinicalDocument).where(
            ClinicalDocument.patient_id == patient_id
        )
        total = (await db.execute(count_q)).scalar() or 0

        result = await db.execute(
            select(ClinicalDocument)
            .where(ClinicalDocument.patient_id == patient_id)
            .order_by(ClinicalDocument.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def list_by_visit(
        db: AsyncSession, visit_id: uuid.UUID
    ) -> Sequence[ClinicalDocument]:
        result = await db.execute(
            select(ClinicalDocument)
            .where(ClinicalDocument.visit_id == visit_id)
            .order_by(ClinicalDocument.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, doc: ClinicalDocument) -> None:
        await db.delete(doc)
        await db.flush()
