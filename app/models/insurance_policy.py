from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import InsuranceProvider, Patient
    from app.models.user import User


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    __table_args__ = (
        CheckConstraint(
            "policy_type IN ('primary', 'secondary', 'dependent')",
            name="ck_insurance_policy_type",
        ),
        CheckConstraint(
            "coverage_type IN ('NHIS', 'HMO', 'Private', 'Corporate', 'Military', 'Tertiary')",
            name="ck_insurance_coverage_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'verified', 'active', 'expired')",
            name="ck_insurance_policy_status",
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
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("insurance_providers.id"),
        nullable=False,
        index=True,
    )
    policy_number: Mapped[str] = mapped_column(String(50), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(20), nullable=False)
    coverage_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    coverage_limit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    copay_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    coinsurance_percentage: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    card_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dependent_patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = sa_relationship(
        foreign_keys="[InsurancePolicy.patient_id]"
    )
    provider: Mapped[InsuranceProvider] = sa_relationship(
        foreign_keys="[InsurancePolicy.provider_id]"
    )
    verifier: Mapped[User | None] = sa_relationship(
        foreign_keys="[InsurancePolicy.verified_by]"
    )
