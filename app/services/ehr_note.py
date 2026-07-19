"""EHR Clinical Note service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ehr_note import EhrNote
from app.schemas.ehr_note import EhrNoteCreate, EhrNoteUpdate
from app.services.audit import AuditService


class EhrNoteService:
    VALID_TRANSITIONS: dict[str, list[str]] = {
        "draft": ["signed"],
        "signed": ["amended"],
        "amended": ["signed"],  # can re-sign after amendment
    }

    @staticmethod
    async def create(
        db: AsyncSession, data: EhrNoteCreate, doctor_id: uuid.UUID
    ) -> EhrNote:
        note = EhrNote(
            visit_id=data.visit_id,
            patient_id=data.patient_id,
            doctor_id=doctor_id,
            subjective=data.subjective,
            objective=data.objective,
            assessment=data.assessment,
            plan=data.plan,
            note_type=data.note_type,
        )
        db.add(note)
        await db.flush()
        await db.refresh(note)
        await AuditService.log(
            db, "ehr_note", note.id, "create",
            detail=f"Clinical note created for visit {data.visit_id}",
        )
        return note

    @staticmethod
    async def get(db: AsyncSession, note_id: uuid.UUID) -> EhrNote | None:
        result = await db.execute(
            select(EhrNote).where(EhrNote.id == note_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_visit(
        db: AsyncSession, visit_id: uuid.UUID
    ) -> Sequence[EhrNote]:
        result = await db.execute(
            select(EhrNote)
            .where(EhrNote.visit_id == visit_id)
            .order_by(EhrNote.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_patient(
        db: AsyncSession, patient_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[EhrNote], int]:
        count_q = select(func.count()).select_from(EhrNote).where(
            EhrNote.patient_id == patient_id
        )
        total = (await db.execute(count_q)).scalar() or 0

        result = await db.execute(
            select(EhrNote)
            .where(EhrNote.patient_id == patient_id)
            .order_by(EhrNote.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def update(
        db: AsyncSession, note: EhrNote, data: EhrNoteUpdate
    ) -> EhrNote:
        if note.status == "signed":
            # Must amend, not edit directly
            if data.amendment_reason:
                note.status = "amended"
                note.amendment_reason = data.amendment_reason
                note.amended_at = datetime.now(timezone.utc)
            else:
                raise ValueError(
                    "Cannot edit a signed note without amendment_reason. "
                    "Use amendment workflow."
                )

        for field, value in data.model_dump(
            exclude_unset=True, exclude={"amendment_reason"}
        ).items():
            setattr(note, field, value)

        await db.flush()
        await db.refresh(note)
        return note

    @staticmethod
    async def sign(db: AsyncSession, note_id: uuid.UUID) -> EhrNote:
        note = await EhrNoteService.get(db, note_id)
        if not note:
            raise ValueError("Note not found")
        if note.status not in EhrNoteService.VALID_TRANSITIONS.get("draft", []):
            raise ValueError(f"Cannot sign note in '{note.status}' status")

        note.status = "signed"
        note.signed_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(note)
        await AuditService.log(
            db, "ehr_note", note.id, "sign",
            detail="Clinical note signed",
        )
        return note

    @staticmethod
    async def delete(db: AsyncSession, note: EhrNote) -> None:
        if note.status == "signed":
            raise ValueError("Cannot delete a signed note")
        await db.delete(note)
        await db.flush()
