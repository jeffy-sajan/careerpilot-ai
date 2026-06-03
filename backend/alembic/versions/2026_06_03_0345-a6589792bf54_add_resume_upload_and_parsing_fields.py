"""add_resume_upload_and_parsing_fields

Revision ID: a6589792bf54
Revises: a1b2c3d4e5f6
Create Date: 2026-06-03 03:45:29.005558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6589792bf54'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enum type in database
    status_enum = sa.Enum('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED', name='resumestatus')
    status_enum.create(op.get_bind(), checkfirst=True)

    # Add columns to resumes table
    op.add_column('resumes', sa.Column('original_file_name', sa.String(length=255), nullable=False))
    op.add_column('resumes', sa.Column('storage_path', sa.String(length=500), nullable=False))
    op.add_column('resumes', sa.Column('content_type', sa.String(length=100), nullable=False))
    op.add_column('resumes', sa.Column('file_size_bytes', sa.Integer(), nullable=False))
    op.add_column('resumes', sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED', name='resumestatus'), nullable=False))
    op.add_column('resumes', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('resumes', sa.Column('parsing_engine_version', sa.String(length=50), nullable=True))

    # Create new indexes
    op.create_index('ix_resumes_created_at', 'resumes', ['created_at'], unique=False)
    op.create_index('ix_resumes_user_id_status', 'resumes', ['user_id', 'status'], unique=False)


def downgrade() -> None:
    # Drop new indexes
    op.drop_index('ix_resumes_user_id_status', table_name='resumes')
    op.drop_index('ix_resumes_created_at', table_name='resumes')

    # Drop columns from resumes table
    op.drop_column('resumes', 'parsing_engine_version')
    op.drop_column('resumes', 'error_message')
    op.drop_column('resumes', 'status')
    op.drop_column('resumes', 'file_size_bytes')
    op.drop_column('resumes', 'content_type')
    op.drop_column('resumes', 'storage_path')
    op.drop_column('resumes', 'original_file_name')

    # Drop Enum type from database
    status_enum = sa.Enum('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED', name='resumestatus')
    status_enum.drop(op.get_bind(), checkfirst=True)

