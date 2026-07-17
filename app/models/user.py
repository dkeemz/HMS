from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.doctor_profile import DoctorProfile
    from app.models.session import UserSession
    from app.models.user_role import UserRole


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'locked', 'suspended')",
            name="ck_user_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_last_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    roles: Mapped[list[UserRole]] = relationship(
        back_populates="user", foreign_keys="[UserRole.user_id]",
    )
    sessions: Mapped[list[UserSession]] = relationship(back_populates="user")
    department: Mapped[Department | None] = relationship(
        "Department", foreign_keys=[department_id], back_populates=None
    )
    headed_departments: Mapped[list[Department]] = relationship(
        "Department", back_populates="head", foreign_keys="Department.head_id"
    )
    doctor_profile: Mapped[DoctorProfile | None] = relationship(
        "DoctorProfile", back_populates="user", uselist=False
    )
