"""Add depth only fields

Revision ID: fe5dce3b6575
Revises: 15e1252a715b
Create Date: 2026-01-27 14:28:05.673232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe5dce3b6575'
down_revision: Union[str, Sequence[str], None] = '15e1252a715b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_depth_only to ver_flowmonitor
    op.add_column('ver_flowmonitor', sa.Column('is_depth_only', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    
    # Add is_depth_only and depth_only_comment to ver_run
    op.add_column('ver_run', sa.Column('is_depth_only', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('ver_run', sa.Column('depth_only_comment', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns
    op.drop_column('ver_run', 'depth_only_comment')
    op.drop_column('ver_run', 'is_depth_only')
    op.drop_column('ver_flowmonitor', 'is_depth_only')
