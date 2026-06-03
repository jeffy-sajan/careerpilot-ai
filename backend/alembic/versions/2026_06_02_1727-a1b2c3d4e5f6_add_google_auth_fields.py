"""Add Google OAuth fields

Revision ID: a1b2c3d4e5f6
Revises: d3ee72c2b403
Create Date: 2026-06-02 17:27:00.000000

Changes:
  - users.password_hash → nullable (Google users have no password)
  - users.google_id      → VARCHAR(255), unique, nullable, indexed
  - users.avatar_url     → VARCHAR(500), nullable
  - users.email_verified → BOOLEAN, default false
  - users.auth_provider  → VARCHAR(20), default 'email'
  - NEW TABLE: google_auth_codes (one-time code pattern for safe token handoff)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd3ee72c2b403'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Alter users table ─────────────────────────────────────────────────────

    # Make password_hash nullable (Google users have no password)
    op.alter_column('users', 'password_hash', existing_type=sa.String(length=255), nullable=True)

    # Add Google OAuth columns
    op.add_column('users', sa.Column('google_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('auth_provider', sa.String(length=20), nullable=False, server_default=sa.text("'email'")))

    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)

    # ── Create google_auth_codes table ────────────────────────────────────────
    op.create_table(
        'google_auth_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('is_new_user', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index(op.f('ix_google_auth_codes_code'), 'google_auth_codes', ['code'], unique=True)
    op.create_index(op.f('ix_google_auth_codes_user_id'), 'google_auth_codes', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop google_auth_codes table
    op.drop_index(op.f('ix_google_auth_codes_user_id'), table_name='google_auth_codes')
    op.drop_index(op.f('ix_google_auth_codes_code'), table_name='google_auth_codes')
    op.drop_table('google_auth_codes')

    # Remove Google columns from users
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'google_id')

    # Restore password_hash to NOT NULL
    op.alter_column('users', 'password_hash', existing_type=sa.String(length=255), nullable=False)
