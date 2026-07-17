from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class FamilyHistory(Base):
    __tablename__ = "family_history"
    __table_args__ = (
        CheckConstraint(
            "status IN ('living', 'deceased')",
            name="ck_family_history_status",
        ),
        Index("ix_family_history_patient_id", "patient_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    condition_name: Mapped[str] = mapped_column(String(200), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    onset_age: Mapped[int | None] = mapped_column(nullable=True)
    icd10_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_hereditary: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="living")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    patient: Mapped[Patient] = sa_relationship(foreign_keys="[FamilyHistory.patient_id]")