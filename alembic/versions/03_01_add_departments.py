"""add departments table

Revision ID: 03_01_add_departments
Revises: manual_0206
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "03_01_add_departments"
down_revision: Union[str, None] = "manual_0206"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_DEPARTMENTS = [
    ("Emergency Medicine", "EMER", "Emergency department for acute care", 1),
    ("Internal Medicine", "IMED", "General internal medicine", 2),
    ("Surgery", "SURG", "Surgical services", 3),
    ("Cardiology", "CARD", "Heart and cardiovascular care", 4),
    ("Pediatrics", "PEDS", "Medical care for infants, children, and adolescents", 5),
    ("Obstetrics & Gynecology", "OBGY", "Women's reproductive health and maternity care", 6),
    ("Orthopedics", "ORTH", "Musculoskeletal system care", 7),
    ("Neurology", "NEUR", "Nervous system disorders", 8),
    ("Radiology", "RAID", "Medical imaging services", 9),
    ("Laboratory", "LABS", "Diagnostic laboratory services", 10),
    ("Pharmacy", "PHRM", "Medication dispensing and inventory", 11),
    ("Administration", "ADMN", "Hospital administration and management", 12),
]


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "head_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("display_order", sa.Integer, server_default=sa.text("0"), nullable=False),
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
            "LENGTH(name) >= 2 AND LENGTH(name) <= 100",
            name="ck_department_name_length",
        ),
        sa.CheckConstraint(
            "LENGTH(code) >= 2 AND LENGTH(code) <= 20",
            name="ck_department_code_length",
        ),
    )

    # Seed default departments
    conn = op.get_bind()
    for name, code, description, display_order in DEFAULT_DEPARTMENTS:
        conn.execute(
            sa.text(
                "INSERT INTO departments (name, code, description, display_order) "
                "VALUES (:name, :code, :description, :display_order) "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"name": name, "code": code, "description": description, "display_order": display_order},
        )

    # Add FK constraint on users.department_id -> departments.id if column exists
    has_col = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_name = 'users' AND column_name = 'department_id'"
            ")"
        )
    ).scalar()
    if has_col:
        has_fk = conn.execute(
            sa.text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.table_constraints "
                "  WHERE constraint_name = 'fk_users_department_id'"
                ")"
            )
        ).scalar()
        if not has_fk:
            op.create_foreign_key(
                "fk_users_department_id",
                "users",
                "departments",
                ["department_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    conn = op.get_bind()
    # Drop FK if it exists
    has_fk = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.table_constraints "
            "  WHERE constraint_name = 'fk_users_department_id'"
            ")"
        )
    ).scalar()
    if has_fk:
        op.drop_constraint("fk_users_department_id", "users", type_="foreignkey")
    op.drop_table("departments")
