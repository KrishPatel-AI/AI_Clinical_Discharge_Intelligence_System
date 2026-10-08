"""add initial_score and actionable suggestion fields

Revision ID: a8b2c3d4e5f6
Revises: cc7a5170229d
Create Date: 2026-10-08 17:55:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "cc7a5170229d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    report_cols = [c["name"] for c in insp.get_columns("reports")]
    suggestion_cols = [c["name"] for c in insp.get_columns("suggestions")]

    with op.batch_alter_table("reports") as batch_op:
        if "initial_score" not in report_cols:
            batch_op.add_column(sa.Column("initial_score", sa.Integer(), nullable=True))

    with op.batch_alter_table("suggestions") as batch_op:
        if "action" not in suggestion_cols:
            batch_op.add_column(
                sa.Column("action", sa.String(length=32), server_default="add", nullable=False)
            )
        if "target_text" not in suggestion_cols:
            batch_op.add_column(
                sa.Column("target_text", sa.Text(), server_default="", nullable=False)
            )
        if "suggested_text" not in suggestion_cols:
            batch_op.add_column(
                sa.Column("suggested_text", sa.Text(), server_default="", nullable=False)
            )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    report_cols = [c["name"] for c in insp.get_columns("reports")]
    suggestion_cols = [c["name"] for c in insp.get_columns("suggestions")]

    with op.batch_alter_table("suggestions") as batch_op:
        if "suggested_text" in suggestion_cols:
            batch_op.drop_column("suggested_text")
        if "target_text" in suggestion_cols:
            batch_op.drop_column("target_text")
        if "action" in suggestion_cols:
            batch_op.drop_column("action")

    with op.batch_alter_table("reports") as batch_op:
        if "initial_score" in report_cols:
            batch_op.drop_column("initial_score")
