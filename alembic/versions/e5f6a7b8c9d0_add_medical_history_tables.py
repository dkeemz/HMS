"""Add medical history tables (allergies, conditions, surgeries, family_history).

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-07-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Allergies table
    op.create_table(
        "allergies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("reaction", sa.String(500), nullable=True),
        sa.Column("onset_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("icd10_code", sa.String(10), nullable=True),
        sa.Column("cross_reactivity_flags", sa.String(200), nullable=True),
        sa.Column("verification_status", sa.String(20), server_default="unverified"),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("corrected_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("allergies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("severity IN ('mild', 'moderate', 'severe', 'life-threatening')", name="ck_allergy_severity"),
        sa.CheckConstraint("status IN ('active', 'corrected', 'resolved')", name="ck_allergy_status"),
        sa.CheckConstraint("verification_status IN ('unverified', 'confirmed', 'ruled-out')", name="ck_allergy_verification"),
        sa.CheckConstraint("source IN ('patient-reported', 'clinical', 'imported')", name="ck_allergy_source"),
    )
    op.create_index("ix_allergies_patient_id", "allergies", ["patient_id"])

    # Conditions table
    op.create_table(
        "conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("clinical_status", sa.String(20), server_default="active"),
        sa.Column("verification_status", sa.String(20), server_default="unconfirmed"),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("onset_date", sa.Date, nullable=True),
        sa.Column("abatement_date", sa.Date, nullable=True),
        sa.Column("icd10_code", sa.String(10), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("clinical_status IN ('active', 'recurrence', 'remission', 'resolved')", name="ck_condition_clinical_status"),
        sa.CheckConstraint("verification_status IN ('unconfirmed', 'provisional', 'differential', 'confirmed')", name="ck_condition_verification"),
        sa.CheckConstraint("severity IN ('mild', 'moderate', 'severe')", name="ck_condition_severity"),
    )
    op.create_index("ix_conditions_patient_id", "conditions", ["patient_id"])

    # Surgeries table
    op.create_table(
        "surgeries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("procedure_date", sa.Date, nullable=False),
        sa.Column("surgeon", sa.String(200), nullable=True),
        sa.Column("facility", sa.String(200), nullable=True),
        sa.Column("outcome", sa.String(200), nullable=True),
        sa.Column("complications", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_surgeries_patient_id", "surgeries", ["patient_id"])

    # Family History table
    op.create_table(
        "family_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("condition_name", sa.String(200), nullable=False),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("onset_age", sa.Integer, nullable=True),
        sa.Column("icd10_code", sa.String(10), nullable=True),
        sa.Column("is_hereditary", sa.Boolean, server_default="false"),
        sa.Column("status", sa.String(20), server_default="living"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('living', 'deceased')", name="ck_family_history_status"),
    )
    op.create_index("ix_family_history_patient_id", "family_history", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_family_history_patient_id", table_name="family_history")
    op.drop_table("family_history")
    op.drop_index("ix_surgeries_patient_id", table_name="surgeries")
    op.drop_table("surgeries")
    op.drop_index("ix_conditions_patient_id", table_name="conditions")
    op.drop_table("conditions")
    op.drop_index("ix_allergies_patient_id", table_name="allergies")
    op.drop_table("allergies")