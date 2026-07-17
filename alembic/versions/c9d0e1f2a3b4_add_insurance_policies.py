"""Add insurance_policies table

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insurance_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            UUID(as_uuid=True),
            sa.ForeignKey("insurance_providers.id"),
            nullable=False,
        ),
        sa.Column("policy_number", sa.String(50), nullable=False),
        sa.Column("policy_type", sa.String(20), nullable=False),
        sa.Column("coverage_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("coverage_limit", sa.Numeric(12, 2), nullable=True),
        sa.Column("copay_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("coinsurance_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("card_image_url", sa.String(500), nullable=True),
        sa.Column("dependent_patient_id", UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", UUID(as_uuid=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "policy_type IN ('primary', 'secondary', 'dependent')",
            name="ck_insurance_policy_type",
        ),
        sa.CheckConstraint(
            "coverage_type IN ('NHIS', 'HMO', 'Private', 'Corporate', 'Military', 'Tertiary')",
            name="ck_insurance_coverage_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'verified', 'active', 'expired')",
            name="ck_insurance_policy_status",
        ),
    )
    op.create_index("ix_insurance_policies_patient_id", "insurance_policies", ["patient_id"])
    op.create_index("ix_insurance_policies_provider_id", "insurance_policies", ["provider_id"])


def downgrade() -> None:
    op.drop_index("ix_insurance_policies_provider_id")
    op.drop_index("ix_insurance_policies_patient_id")
    op.drop_table("insurance_policies")
