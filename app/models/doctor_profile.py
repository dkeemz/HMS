"""Doctor profile — extends User with medical professional data."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    __table_args__ = (
        CheckConstraint(
            "availability_status IN ('available', 'on-leave', 'in-surgery', 'on-duty', 'unavailable')",
            name="ck_doctor_availability_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    specialty: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sub_specialty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    qualifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    consultation_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consultation_fee: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_accepting_patients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    availability_status: Mapped[str] = mapped_column(String(20), default="available", nullable=False)
    last_status_change_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="doctor_profile")

    def __repr__(self) -> str:
        return f"<DoctorProfile {self.specialty}: {self.user_id}>"
