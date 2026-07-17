"""Add audit log partitioning by month.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-14

"""

from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename existing table to hold data during conversion
    op.execute("ALTER TABLE audit_logs RENAME TO audit_logs_old;")

    # Create the partitioned parent table with the same schema
    op.execute("""
        CREATE TABLE audit_logs (
            id UUID DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            action VARCHAR(50) NOT NULL,
            resource VARCHAR(50) NOT NULL,
            resource_id VARCHAR(255),
            metadata JSONB,
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            previous_hash VARCHAR(64),
            hash VARCHAR(64) NOT NULL,
            patient_id UUID,
            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp);
    """)

    # Create monthly partitions for current and next year
    op.execute("""
        CREATE TABLE audit_logs_default
        PARTITION OF audit_logs DEFAULT;
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_01
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_02
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_03
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_04
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_05
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_06
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_07
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_08
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_09
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_10
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_11
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_12
        PARTITION OF audit_logs
        FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
    """)

    # Migrate existing data
    op.execute("""
        INSERT INTO audit_logs
        SELECT * FROM audit_logs_old;
    """)

    # Drop old table
    op.execute("DROP TABLE audit_logs_old;")

    # Create indexes (inherited automatically by partitions, but created on parent)
    op.execute("""
        CREATE INDEX idx_audit_logs_timestamp ON audit_logs (timestamp);
    """)
    op.execute("""
        CREATE INDEX idx_audit_logs_user_id ON audit_logs (user_id);
    """)
    op.execute("""
        CREATE INDEX idx_audit_logs_patient_id ON audit_logs (patient_id);
    """)
    op.execute("""
        CREATE INDEX idx_audit_logs_action ON audit_logs (action);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE;")
    # Restore from old if it exists (best-effort; data may be lost)
    op.execute("""
        ALTER TABLE IF EXISTS audit_logs_old RENAME TO audit_logs;
    """)
