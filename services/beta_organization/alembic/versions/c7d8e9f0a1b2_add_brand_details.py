"""Add manufacturer and notes to tenant-scoped brands."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "v2b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "brands",
        sa.Column("manufacturer", sa.String(length=180), nullable=False, server_default=""),
        schema="ferti",
    )
    op.add_column(
        "brands",
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        schema="ferti",
    )


def downgrade() -> None:
    op.drop_column("brands", "notes", schema="ferti")
    op.drop_column("brands", "manufacturer", schema="ferti")
