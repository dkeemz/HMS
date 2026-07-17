from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.visit import Visit


class VisitSummary(Base):
    __tablename__ = "visit_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visits.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    doctor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnoses: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prescriptions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    procedures_performed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    lab_orders: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    visit: Mapped[Visit] = sa_relationship(back_populates="summary")
