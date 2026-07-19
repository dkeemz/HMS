"""Lab Results model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User
    from app.models.visit import Visit


class LabResult(Base):
    """Lab test result linked to a patient visit."""

    __tablename__ = "lab_results"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ordered', 'in_progress', 'completed', 'cancelled')",
            name="ck_lab_results_status",
        ),
        CheckConstraint(
            "abnormal_flag IN ('normal', 'high', 'low', 'critical_high', 'critical_low')",
            name="ck_lab_results_abnormal",
        ),
        CheckConstraint(
            "category IN ('hematology', 'chemistry', 'urinalysis', 'microbiology', 'pathology', 'immunology', 'endocrinology', 'other')",
            name="ck_lab_results_category",
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
    ordered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Test info
    test_name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(30), default="chemistry")
    clinical_question: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Result
    result_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    result_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    abnormal_flag: Mapped[str] = mapped_column(String(20), default="normal")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="ordered")
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    visit: Mapped[Visit] = sa_relationship(back_populates="lab_results")
    patient: Mapped[Patient] = sa_relationship(back_populates="lab_results")
    orderer: Mapped[User] = sa_relationship(foreign_keys=[ordered_by])
    completer: Mapped[User] = sa_relationship(foreign_keys=[completed_by])

    def __repr__(self) -> str:
        return f"<LabResult {self.test_name} status={self.status}>"
