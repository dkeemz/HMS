"""add doctor_profiles table

Revision ID: 03_02_add_doctor_profiles
Revises: 03_01_add_departments
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "03_02_add_doctor_profiles"
down_revision: Union[str, None] = "03_01_add_departments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("specialty", sa.String(100), nullable=False),
        sa.Column("sub_specialty", sa.String(100), nullable=True),
        sa.Column("license_number", sa.String(50), nullable=False, unique=True),
        sa.Column("qualifications", postgresql.JSONB, nullable=True),
        sa.Column("consultation_hours", postgresql.JSONB, nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("years_of_experience", sa.Integer, nullable=True),
        sa.Column("consultation_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column(
            "is_accepting_patients",
            sa.Boolean,
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "availability_status",
            sa.String(20),
            server_default=sa.text("'available'"),
            nullable=False,
        ),
        sa.Column(
            "last_status_change_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "availability_status IN ('available', 'on-leave', 'in-surgery', 'on-duty', 'unavailable')",
            name="ck_doctor_availability_status",
        ),
    )
    op.create_index(
        "ix_doctor_profiles_user_id",
        "doctor_profiles",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_doctor_profiles_specialty",
        "doctor_profiles",
        ["specialty"],
    )


def downgrade() -> None:
    op.drop_index("ix_doctor_profiles_specialty", table_name="doctor_profiles")
    op.drop_index("ix_doctor_profiles_user_id", table_name="doctor_profiles")
    op.drop_table("doctor_profiles")
