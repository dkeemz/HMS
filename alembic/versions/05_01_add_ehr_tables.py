"""Add EHR tables: ehr_notes, vital_signs, diagnoses, lab_results, clinical_documents

Revision ID: 05_01_add_ehr
Revises: 04_01_add_appointments
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "05_01_add_ehr"
down_revision = "04_01_add_appointments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ehr_notes ─────────────────────────────────────────────────────
    op.create_table(
        "ehr_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("encounter_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("subjective", sa.Text, server_default=""),
        sa.Column("objective", sa.Text, server_default=""),
        sa.Column("assessment", sa.Text, server_default=""),
        sa.Column("plan", sa.Text, server_default=""),
        sa.Column("note_type", sa.String(30), server_default="consultation"),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amendment_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── vital_signs ───────────────────────────────────────────────────
    op.create_table(
        "vital_signs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("systolic_bp", sa.Integer, nullable=True),
        sa.Column("diastolic_bp", sa.Integer, nullable=True),
        sa.Column("heart_rate", sa.Integer, nullable=True),
        sa.Column("respiratory_rate", sa.Integer, nullable=True),
        sa.Column("temperature", sa.Numeric(4, 1), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=True),
        sa.Column("height_cm", sa.Numeric(5, 1), nullable=True),
        sa.Column("spo2", sa.Integer, nullable=True),
        sa.Column("pain_level", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── diagnoses ─────────────────────────────────────────────────────
    op.create_table(
        "diagnoses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("icd_code", sa.String(20), nullable=False),
        sa.Column("icd_version", sa.String(2), server_default="10"),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("diagnosis_type", sa.String(20), server_default="primary"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("onset_date", sa.Date, nullable=True),
        sa.Column("resolved_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("diagnosis_type IN ('primary', 'secondary', 'differential')", name="ck_diagnoses_type"),
        sa.CheckConstraint("status IN ('active', 'resolved', 'ruled_out')", name="ck_diagnoses_status"),
        sa.CheckConstraint("icd_version IN ('10', '11')", name="ck_diagnoses_icd_version"),
    )

    # ── lab_results ───────────────────────────────────────────────────
    op.create_table(
        "lab_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ordered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("test_name", sa.String(300), nullable=False),
        sa.Column("category", sa.String(30), server_default="chemistry"),
        sa.Column("clinical_question", sa.String(500), nullable=True),
        sa.Column("result_value", sa.String(200), nullable=True),
        sa.Column("result_unit", sa.String(50), nullable=True),
        sa.Column("reference_range", sa.String(100), nullable=True),
        sa.Column("abnormal_flag", sa.String(20), server_default="normal"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), server_default="ordered"),
        sa.Column("ordered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('ordered', 'in_progress', 'completed', 'cancelled')", name="ck_lab_results_status"),
        sa.CheckConstraint("abnormal_flag IN ('normal', 'high', 'low', 'critical_high', 'critical_low')", name="ck_lab_results_abnormal"),
        sa.CheckConstraint("category IN ('hematology', 'chemistry', 'urinalysis', 'microbiology', 'pathology', 'immunology', 'endocrinology', 'other')", name="ck_lab_results_category"),
    )

    # ── clinical_documents ────────────────────────────────────────────
    op.create_table(
        "clinical_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_type", sa.String(20), server_default="report"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.BigInteger, nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "document_type IN ('scan', 'image', 'report', 'lab_report', 'prescription', 'referral', 'other')",
            name="ck_clinical_docs_type",
        ),
    )


def downgrade() -> None:
    op.drop_table("clinical_documents")
    op.drop_table("lab_results")
    op.drop_table("diagnoses")
    op.drop_table("vital_signs")
    op.drop_table("ehr_notes")
