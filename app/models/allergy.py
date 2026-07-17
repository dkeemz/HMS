from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class Allergy(Base):
    __tablename__ = "allergies"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('mild', 'moderate', 'severe', 'life-threatening')",
            name="ck_allergy_severity",
        ),
        CheckConstraint(
            "status IN ('active', 'corrected', 'resolved')",
            name="ck_allergy_status",
        ),
        CheckConstraint(
            "verification_status IN ('unverified', 'confirmed', 'ruled-out')",
            name="ck_allergy_verification",
        ),
        CheckConstraint(
            "source IN ('patient-reported', 'clinical', 'imported')",
            name="ck_allergy_source",
        ),
        Index("ix_allergies_patient_id", "patient_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    reaction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    icd10_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cross_reactivity_flags: Mapped[str | None] = mapped_column(String(200), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified")
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    corrected_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("allergies.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = sa_relationship(foreign_keys="[Allergy.patient_id]")
