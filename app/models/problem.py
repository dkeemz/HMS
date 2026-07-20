from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = ({"schema": None},)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_name: Mapped[str] = mapped_column(String(300), nullable=False)
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    icd_version: Mapped[str] = mapped_column(String(2), default="10")
    status: Mapped[str] = mapped_column(String(20), default="active")
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    laterality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    chronicity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped[Patient] = sa_relationship(back_populates="problems")

    def __repr__(self) -> str:
        return f"<Problem {self.id} {self.problem_name} status={self.status}>"
