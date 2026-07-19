"""Appointment model — scheduling core for Phase 4."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled','confirmed','checked-in','in-progress','completed','cancelled','no-show','rescheduled')",
            name="ck_appointment_status",
        ),
        CheckConstraint(
            "appointment_type IN ('consultation','follow-up','procedure','emergency','lab','vaccination','other')",
            name="ck_appointment_type",
        ),
        CheckConstraint(
            "priority IN ('low','normal','high','urgent')",
            name="ck_appointment_priority",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    appointment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="consultation")
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled", index=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="normal")
    room: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rescheduled_from: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    queue_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # Relationships
    patient = sa_relationship("Patient", foreign_keys=[patient_id], back_populates=None, lazy="selectin")
    doctor = sa_relationship("User", foreign_keys=[doctor_id], back_populates=None, lazy="selectin")
    department = sa_relationship("Department", foreign_keys=[department_id], back_populates=None, lazy="selectin")

    def __repr__(self) -> str:
        return f"<Appointment {self.appointment_type}: {self.scheduled_at}>"
