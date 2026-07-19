"""Diagnosis model."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User
    from app.models.visit import Visit


class Diagnosis(Base):
    """ICD-10/11 diagnosis linked to a patient visit."""

    __tablename__ = "diagnoses"
    __table_args__ = (
        CheckConstraint(
            "diagnosis_type IN ('primary', 'secondary', 'differential')",
            name="ck_diagnoses_type",
        ),
        CheckConstraint(
            "status IN ('active', 'resolved', 'ruled_out')",
            name="ck_diagnoses_status",
        ),
        CheckConstraint(
            "icd_version IN ('10', '11')",
            name="ck_diagnoses_icd_version",
        ),
        {"schema": None},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    icd_code: Mapped[str] = mapped_column(String(20), nullable=False)
    icd_version: Mapped[str] = mapped_column(String(2), default="10")
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    diagnosis_type: Mapped[str] = mapped_column(String(20), default="primary")
    status: Mapped[str] = mapped_column(String(20), default="active")

    onset_date: Mapped[date | None] = mapped_column(nullable=True)
    resolved_date: Mapped[date | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    visit: Mapped[Visit] = sa_relationship(back_populates="diagnoses")
    patient: Mapped[Patient] = sa_relationship(back_populates="diagnoses")
    doctor: Mapped[User] = sa_relationship(foreign_keys=[doctor_id])

    def __repr__(self) -> str:
        return f"<Diagnosis {self.icd_code} ({self.description})>"
