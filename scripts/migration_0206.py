"""add visits and visit_summaries tables

Revision ID: manual_0206
Revises: c9d0e1f2a3b4
Create Date: 2026-07-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "manual_0206"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create visits table
    op.create_table(
        "visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("reason_notes", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), server_default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("cancellation_reason", sa.String(200), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "reason IN ('consultation', 'follow-up', 'procedure', 'emergency', 'lab', 'vaccination', 'other')",
            name="ck_visit_reason",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'checked-in', 'in-progress', 'completed', 'cancelled')",
            name="ck_visit_status",
        ),
    )
    op.create_index("ix_visits_patient_id", "visits", ["patient_id"])

    # Create visit_summaries table
    op.create_table(
        "visit_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("doctor_name", sa.String(200), nullable=True),
        sa.Column("diagnosis", sa.Text, nullable=True),
        sa.Column("diagnoses", postgresql.JSON, nullable=True),
        sa.Column("prescriptions", postgresql.JSON, nullable=True),
        sa.Column("procedures_performed", postgresql.JSON, nullable=True),
        sa.Column("lab_orders", postgresql.JSON, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("visit_summaries")
    op.drop_index("ix_visits_patient_id", table_name="visits")
    op.drop_table("visits")
