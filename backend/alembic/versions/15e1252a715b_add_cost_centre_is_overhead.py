"""add_cost_centre_is_overhead

Revision ID: 15e1252a715b
Revises: 3118222ed90d
Create Date: 2026-01-06 10:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15e1252a715b'
down_revision: Union[str, Sequence[str], None] = '3118222ed90d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_overhead column to admin_cost_centre."""
    op.add_column('admin_cost_centre', 
        sa.Column('is_overhead', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove is_overhead column from admin_cost_centre."""
    op.drop_column('admin_cost_centre', 'is_overhead')
