"""add_patient_tables

Revision ID: d4e5f6a7b8c9
Revises: c4d5e6f7a8b9
Create Date: 2026-07-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── patients ──────────────────────────────────────────────────────────
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mrn", sa.String(20), unique=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("blood_group", sa.String(5), nullable=True),
        sa.Column("nin", sa.String(11), nullable=True),
        sa.Column("preferred_language", sa.String(20), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("address_street", sa.String(255), nullable=False),
        sa.Column("address_city", sa.String(100), nullable=False),
        sa.Column("address_state", sa.String(100), nullable=False),
        sa.Column("address_lga", sa.String(100), nullable=True),
        sa.Column("address_postal_code", sa.String(10), nullable=True),
        sa.Column("address_landmark", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'deceased')",
            name="ck_patient_status",
        ),
    )
    op.create_index("ix_patients_mrn", "patients", ["mrn"], unique=True)
    op.create_index("ix_patients_status", "patients", ["status"])

    # GIN indexes for pg_trgm fuzzy search
    op.execute(
        "CREATE INDEX ix_patient_name_trgm ON patients "
        "USING gin ((first_name || ' ' || last_name) gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_patient_mrn_trgm ON patients "
        "USING gin (mrn gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_patient_phone_trgm ON patients "
        "USING gin (phone gin_trgm_ops)"
    )

    # ── emergency_contacts ────────────────────────────────────────────────
    op.create_table(
        "emergency_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("relationship", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_emergency_contacts_patient_id", "emergency_contacts", ["patient_id"])

    # ── next_of_kin ──────────────────────────────────────────────────────
    op.create_table(
        "next_of_kin",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("relationship", sa.String(50), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_next_of_kin_patient_id", "next_of_kin", ["patient_id"])

    # ── consents ─────────────────────────────────────────────────────────
    op.create_table(
        "consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("template_name", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("signed_by", sa.String(200), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_consents_patient_id", "consents", ["patient_id"])

    # ── mrn_sequences ────────────────────────────────────────────────────
    op.create_table(
        "mrn_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("facility_prefix", sa.String(10), unique=True, nullable=False),
        sa.Column("facility_name", sa.String(100), nullable=False),
        sa.Column("last_value", sa.Integer, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── insurance_providers ──────────────────────────────────────────────
    op.create_table(
        "insurance_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("short_code", sa.String(20), unique=True, nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── Add FK constraints to existing tables ────────────────────────────
    op.alter_column(
        "break_glass_access",
        "patient_id",
        existing_type=postgresql.UUID(as_uuid=True),
        foreign_key=sa.ForeignKey("patients.id", ondelete="CASCADE"),
    )


def downgrade() -> None:
    # Drop FK constraints on existing tables first
    op.drop_constraint("break_glass_access_patient_id_fkey", "break_glass_access", type_="foreignkey")

    # Drop tables in reverse FK order
    op.drop_table("insurance_providers")
    op.drop_table("mrn_sequences")
    op.drop_table("consents")
    op.drop_table("next_of_kin")
    op.drop_table("emergency_contacts")

    # Drop GIN indexes (implicitly dropped with table drop, but explicit for safety)
    op.execute("DROP INDEX IF EXISTS ix_patient_phone_trgm")
    op.execute("DROP INDEX IF EXISTS ix_patient_mrn_trgm")
    op.execute("DROP INDEX IF EXISTS ix_patient_name_trgm")
    op.drop_table("patients")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
