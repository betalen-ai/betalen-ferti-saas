"""add is_super_admin to org_users

Revision ID: a1b2c3d4e5f7
Revises: fcd31bb21c84
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "fcd31bb21c84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE org.org_users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN NOT NULL DEFAULT false
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE org.org_users DROP COLUMN IF EXISTS is_super_admin")