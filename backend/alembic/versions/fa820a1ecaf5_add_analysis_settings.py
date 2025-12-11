"""add_analysis_settings

Revision ID: fa820a1ecaf5
Revises: 1a2b3c4d5e6f
Create Date: 2025-12-11 22:51:06.198839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa820a1ecaf5'
down_revision: Union[str, Sequence[str], None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('verificationrun', sa.Column('analysis_settings', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('verificationrun', 'analysis_settings')
