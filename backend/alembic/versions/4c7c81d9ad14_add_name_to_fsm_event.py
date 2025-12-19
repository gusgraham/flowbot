"""add_name_to_fsm_event

Revision ID: 4c7c81d9ad14
Revises: 68650b2a5b67
Create Date: 2025-12-18 10:18:16.822736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '4c7c81d9ad14'
down_revision: Union[str, Sequence[str], None] = '68650b2a5b67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Manual edit: Only apply the ADD COLUMN, skip drops to avoid index errors on legacy tables
    op.add_column('fsm_event', sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('fsm_event', 'name')
