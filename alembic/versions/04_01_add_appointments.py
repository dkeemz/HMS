"""add appointments table

Revision ID: 04_01_add_appointments
Revises: 03_02_add_doctor_profiles
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "04_01_add_appointments"
down_revision: Union[str, None] = "03_02_add_doctor_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("appointment_type", sa.String(30), nullable=False, server_default="consultation"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="15"),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled", index=True),
        sa.Column("priority", sa.String(10), nullable=False, server_default="normal"),
        sa.Column("room", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("cancellation_reason", sa.String(200), nullable=True),
        sa.Column("rescheduled_from", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("queue_position", sa.Integer, nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('scheduled','confirmed','checked-in','in-progress','completed','cancelled','no-show','rescheduled')",
            name="ck_appointment_status",
        ),
        sa.CheckConstraint(
            "appointment_type IN ('consultation','follow-up','procedure','emergency','lab','vaccination','other')",
            name="ck_appointment_type",
        ),
        sa.CheckConstraint(
            "priority IN ('low','normal','high','urgent')",
            name="ck_appointment_priority",
        ),
    )

    # Add FK constraints on visits table for appointment_id and department_id
    conn = op.get_bind()

    # visits.appointment_id -> appointments.id
    has_col = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='visits' AND column_name='appointment_id')")
    ).scalar()
    if has_col:
        has_fk = conn.execute(
            sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_visits_appointment_id')")
        ).scalar()
        if not has_fk:
            op.create_foreign_key(
                "fk_visits_appointment_id", "visits", "appointments",
                ["appointment_id"], ["id"], ondelete="SET NULL",
            )

    # visits.department_id -> departments.id
    has_col = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='visits' AND column_name='department_id')")
    ).scalar()
    if has_col:
        has_fk = conn.execute(
            sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_visits_department_id')")
        ).scalar()
        if not has_fk:
            op.create_foreign_key(
                "fk_visits_department_id", "visits", "departments",
                ["department_id"], ["id"], ondelete="SET NULL",
            )


def downgrade() -> None:
    conn = op.get_bind()
    # Drop visit FKs
    for cname in ("fk_visits_appointment_id", "fk_visits_department_id"):
        has_fk = conn.execute(
            sa.text(f"SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='{cname}')")
        ).scalar()
        if has_fk:
            op.drop_constraint(cname, "visits", type_="foreignkey")
    op.drop_table("appointments")
