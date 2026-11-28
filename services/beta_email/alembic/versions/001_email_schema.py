"""Create beta_email schema tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "001_email_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS email")
    op.create_table(
        "email_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255)),
        sa.Column("user_id", sa.String(255)),
        sa.Column("template", sa.String(64), nullable=False),
        sa.Column("locale", sa.String(8), nullable=False),
        sa.Column("to_email", sa.String(320), nullable=False),
        sa.Column("to_name", sa.String(255)),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("payload_encrypted", sa.Text()),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("idempotency_hash", sa.String(64)),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("provider", sa.String(32)),
        sa.Column("provider_message_id", sa.String(255)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("request_id", sa.String(255)),
        sa.Column("caller_service", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("caller_service", "idempotency_key", name="uq_email_idempotency"),
        schema="email",
    )
    op.create_table(
        "email_attempts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("result", sa.String(32), nullable=False),
        sa.Column("smtp_code", sa.Integer()),
        sa.Column("error_text", sa.Text()),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        schema="email",
    )
    op.create_table(
        "email_suppressions",
        sa.Column("email", sa.String(320), primary_key=True),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        schema="email",
    )


def downgrade() -> None:
    op.drop_table("email_suppressions", schema="email")
    op.drop_table("email_attempts", schema="email")
    op.drop_table("email_messages", schema="email")
