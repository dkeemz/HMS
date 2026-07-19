"""Clinical Documents model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User
    from app.models.visit import Visit


class ClinicalDocument(Base):
    """Uploaded clinical document (scan, image, report) attached to a patient."""

    __tablename__ = "clinical_documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('scan', 'image', 'report', 'lab_report', 'prescription', 'referral', 'other')",
            name="ck_clinical_docs_type",
        ),
        {"schema": None},
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
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    document_type: Mapped[str] = mapped_column(String(20), default="report")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # File info
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    patient: Mapped[Patient] = sa_relationship(back_populates="clinical_documents")
    visit: Mapped[Visit] = sa_relationship(back_populates="documents")
    uploader: Mapped[User] = sa_relationship(foreign_keys=[uploaded_by])

    def __repr__(self) -> str:
        return f"<ClinicalDocument {self.title}>"
