"""Add access_ssd column to user table

Revision ID: b0bcce7e4ac5
Revises: a5d829c8b2e1
Create Date: 2025-12-09 15:46:43.930853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b0bcce7e4ac5'
down_revision: Union[str, Sequence[str], None] = 'a5d829c8b2e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add access_ssd column with a default value of True (1)
    op.add_column('user', sa.Column('access_ssd', sa.Boolean(), nullable=False, server_default=sa.text('1')))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'access_ssd')
