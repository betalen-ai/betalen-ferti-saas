"""align onboarding auth schema

Revision ID: fcd31bb21c84
Revises: e1f2a3b4c5d6
"""
from typing import Sequence, Union

from alembic import op


revision: str = "fcd31bb21c84"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_ferti_refresh_sessions_family_id ON ferti.refresh_sessions (family_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_otp_requests_phone ON org.otp_requests (phone)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_tenant_documents_tenant_id ON org.tenant_documents (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_tenant_reviews_tenant_id ON org.tenant_reviews (tenant_id)")
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_org_user_email' AND conrelid = 'org.org_users'::regclass
        ) THEN
            ALTER TABLE org.org_users DROP CONSTRAINT IF EXISTS uq_org_user_tenant_email;
            ALTER TABLE org.org_users ADD CONSTRAINT uq_org_user_email UNIQUE (email);
        END IF;
    END $$;
    """)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_org_refresh_token_hash' AND conrelid = 'org.refresh_tokens'::regclass
        ) THEN
            ALTER TABLE org.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_token_hash_key;
            ALTER TABLE org.refresh_tokens ADD CONSTRAINT uq_org_refresh_token_hash UNIQUE (token_hash);
        END IF;
    END $$;
    """)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_org_tenant_reference_no' AND conrelid = 'org.tenants'::regclass
        ) THEN
            ALTER TABLE org.tenants ADD CONSTRAINT uq_org_tenant_reference_no UNIQUE (reference_no);
        END IF;
    END $$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ferti.ix_ferti_refresh_sessions_family_id")
    op.execute("DROP INDEX IF EXISTS org.ix_org_otp_requests_phone")
    op.execute("DROP INDEX IF EXISTS org.ix_org_tenant_documents_tenant_id")
    op.execute("DROP INDEX IF EXISTS org.ix_org_tenant_reviews_tenant_id")
    op.execute("ALTER TABLE org.tenants DROP CONSTRAINT IF EXISTS uq_org_tenant_reference_no")
    op.execute("ALTER TABLE org.refresh_tokens DROP CONSTRAINT IF EXISTS uq_org_refresh_token_hash")
    op.execute("ALTER TABLE org.refresh_tokens ADD CONSTRAINT refresh_tokens_token_hash_key UNIQUE (token_hash)")
    op.execute("ALTER TABLE org.org_users DROP CONSTRAINT IF EXISTS uq_org_user_email")
    op.execute("ALTER TABLE org.org_users ADD CONSTRAINT uq_org_user_tenant_email UNIQUE (tenant_id, email)")
