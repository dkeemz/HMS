"""Vital Signs model."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User
    from app.models.visit import Visit


class VitalSign(Base):
    """Patient vital signs recorded during a visit."""

    __tablename__ = "vital_signs"
    __table_args__ = ({"schema": None},)

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
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Blood pressure
    systolic_bp: Mapped[int | None] = mapped_column(nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(nullable=True)

    # Heart & respiration
    heart_rate: Mapped[int | None] = mapped_column(nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(nullable=True)

    # Temperature
    temperature: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )

    # Body measurements
    weight_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    height_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 1), nullable=True
    )

    # Oxygen saturation
    spo2: Mapped[int | None] = mapped_column(nullable=True)

    # Pain scale (0-10)
    pain_level: Mapped[int | None] = mapped_column(nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    visit: Mapped[Visit] = sa_relationship(back_populates="vitals")
    patient: Mapped[Patient] = sa_relationship(back_populates="vital_signs")
    recorder: Mapped[User] = sa_relationship(foreign_keys=[recorded_by])

    @property
    def bmi(self) -> float | None:
        """Compute BMI if height and weight are available."""
        if self.weight_kg and self.height_cm:
            h_m = float(self.height_cm) / 100
            if h_m > 0:
                return round(float(self.weight_kg) / (h_m * h_m), 1)
        return None

    def __repr__(self) -> str:
        return f"<VitalSign {self.id} visit={self.visit_id}>"
