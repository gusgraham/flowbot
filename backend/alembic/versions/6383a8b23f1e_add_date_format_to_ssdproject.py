"""add_date_format_to_ssdproject

Revision ID: 6383a8b23f1e
Revises: 0bbd17bb36fb
Create Date: 2025-12-09 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6383a8b23f1e'
down_revision: Union[str, Sequence[str], None] = '0bbd17bb36fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add date_format column to ssdproject table."""
    op.add_column('ssdproject', sa.Column('date_format', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove date_format column."""
    op.drop_column('ssdproject', 'date_format')
