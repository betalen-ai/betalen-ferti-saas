"""initial org tables

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-11-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS org")

    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subdomain', sa.String(), unique=True),
        sa.Column('subscription_plan', sa.String(), server_default='free'),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        schema='org'
    )

    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        schema='org'
    )

    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),
        schema='org'
    )

    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.permissions.id', ondelete='CASCADE'), primary_key=True),
        schema='org'
    )

    op.create_table(
        'org_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String()),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.roles.id')),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_org_user_tenant_email'),
        schema='org'
    )

    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        schema='org'
    )


def downgrade() -> None:
    op.drop_table('subscriptions', schema='org')
    op.drop_table('org_users', schema='org')
    op.drop_table('role_permissions', schema='org')
    op.drop_table('permissions', schema='org')
    op.drop_table('roles', schema='org')
    op.drop_table('tenants', schema='org')
    op.execute("DROP SCHEMA IF EXISTS org CASCADE")
