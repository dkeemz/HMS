"""Drop unique constraint on keycloak_session_id.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-16
"""
from alembic import op

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "user_sessions_keycloak_session_id_key", "user_sessions", type_="unique"
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "user_sessions_keycloak_session_id_key",
        "user_sessions",
        ["keycloak_session_id"],
    )
