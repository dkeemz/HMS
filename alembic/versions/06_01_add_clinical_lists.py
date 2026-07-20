"""Add clinical lists tables: problems, medications

Revision ID: 06_01_add_clinical_lists
Revises: 05_01_add_ehr
Create Date: 2026-07-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "06_01_add_clinical_lists"
down_revision = "05_01_add_ehr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # problems
    op.create_table(
        "problems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("problem_name", sa.String(300), nullable=False),
        sa.Column("icd_code", sa.String(20), nullable=True),
        sa.Column("icd_version", sa.String(2), nullable=False, server_default="10"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("onset_date", sa.Date(), nullable=True),
        sa.Column("resolved_date", sa.Date(), nullable=True),
        sa.Column("laterality", sa.String(20), nullable=True),
        sa.Column("chronicity", sa.String(30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # medications
    op.create_table(
        "medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("prescribed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("medication_name", sa.String(300), nullable=False),
        sa.Column("generic_name", sa.String(300), nullable=True),
        sa.Column("strength", sa.String(100), nullable=True),
        sa.Column("dosage_form", sa.String(50), nullable=True),
        sa.Column("frequency", sa.String(100), nullable=True),
        sa.Column("route", sa.String(50), nullable=True),
        sa.Column("duration", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("refills", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("medications")
    op.drop_table("problems")
