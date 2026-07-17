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


class Condition(Base):
    __tablename__ = "conditions"
    __table_args__ = (
        CheckConstraint(
            "clinical_status IN ('active', 'recurrence', 'remission', 'resolved')",
            name="ck_condition_clinical_status",
        ),
        CheckConstraint(
            "verification_status IN ('unconfirmed', 'provisional', 'differential', 'confirmed')",
            name="ck_condition_verification",
        ),
        CheckConstraint(
            "severity IN ('mild', 'moderate', 'severe')",
            name="ck_condition_severity",
        ),
        Index("ix_conditions_patient_id", "patient_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    clinical_status: Mapped[str] = mapped_column(String(20), default="active")
    verification_status: Mapped[str] = mapped_column(String(20), default="unconfirmed")
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    abatement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    icd10_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
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

    patient: Mapped[Patient] = sa_relationship(foreign_keys="[Condition.patient_id]")