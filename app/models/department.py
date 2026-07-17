"""Department model — hierarchical organizational structure."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        CheckConstraint(
            "LENGTH(name) >= 2 AND LENGTH(name) <= 100",
            name="ck_department_name_length",
        ),
        CheckConstraint(
            "LENGTH(code) >= 2 AND LENGTH(code) <= 20",
            name="ck_department_code_length",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    head_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    parent = relationship("Department", remote_side="Department.id", back_populates="children")
    children = relationship("Department", back_populates="parent")
    head = relationship("User", foreign_keys=[head_id], back_populates="headed_departments")

    def __repr__(self) -> str:
        return f"<Department {self.code}: {self.name}>"
