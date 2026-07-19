from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Date, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.allergy import Allergy
    from app.models.condition import Condition
    from app.models.consent import Consent
    from app.models.emergency_contact import EmergencyContact
    from app.models.family_history import FamilyHistory
    from app.models.next_of_kin import NextOfKin
    from app.models.surgery import Surgery


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'deceased')",
            name="ck_patient_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mrn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(5), nullable=True)
    nin: Mapped[str | None] = mapped_column(String(11), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    address_street: Mapped[str] = mapped_column(String(255), nullable=False)
    address_city: Mapped[str] = mapped_column(String(100), nullable=False)
    address_state: Mapped[str] = mapped_column(String(100), nullable=False)
    address_lga: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    address_landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    emergency_contacts: Mapped[list[EmergencyContact]] = sa_relationship(
        back_populates="patient", foreign_keys="[EmergencyContact.patient_id]",
    )
    next_of_kin: Mapped[list[NextOfKin]] = sa_relationship(
        back_populates="patient", foreign_keys="[NextOfKin.patient_id]",
    )
    consents: Mapped[list[Consent]] = sa_relationship(
        back_populates="patient", foreign_keys="[Consent.patient_id]",
    )
    allergies: Mapped[list[Allergy]] = sa_relationship(
        back_populates="patient", foreign_keys="[Allergy.patient_id]",
    )
    conditions: Mapped[list[Condition]] = sa_relationship(
        back_populates="patient", foreign_keys="[Condition.patient_id]",
    )
    surgeries: Mapped[list[Surgery]] = sa_relationship(
        back_populates="patient", foreign_keys="[Surgery.patient_id]",
    )
    family_history: Mapped[list[FamilyHistory]] = sa_relationship(
        back_populates="patient", foreign_keys="[FamilyHistory.patient_id]",
    )
    ehr_notes: Mapped[list] = sa_relationship(
        back_populates="patient", foreign_keys="[EhrNote.patient_id]",
    )
    vital_signs: Mapped[list] = sa_relationship(
        back_populates="patient", foreign_keys="[VitalSign.patient_id]",
    )
    diagnoses: Mapped[list] = sa_relationship(
        back_populates="patient", foreign_keys="[Diagnosis.patient_id]",
    )
    lab_results: Mapped[list] = sa_relationship(
        back_populates="patient", foreign_keys="[LabResult.patient_id]",
    )
    clinical_documents: Mapped[list] = sa_relationship(
        back_populates="patient", foreign_keys="[ClinicalDocument.patient_id]",
    )


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = sa_relationship(back_populates="emergency_contacts")


class NextOfKin(Base):
    __tablename__ = "next_of_kin"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = sa_relationship(back_populates="next_of_kin")


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    signed_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = sa_relationship(back_populates="consents")


class MrnSequence(Base):
    __tablename__ = "mrn_sequences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    facility_prefix: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    facility_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_value: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    short_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
