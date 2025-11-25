"""add_analysis_timeseries_table

Revision ID: f00f6e5349a9
Revises: 6a998ea89017
Create Date: 2025-11-25 14:18:50.987899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f00f6e5349a9'
down_revision: Union[str, Sequence[str], None] = '6a998ea89017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'analysistimeseries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['analysisdataset.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysistimeseries_dataset_id'), 'analysistimeseries', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_analysistimeseries_timestamp'), 'analysistimeseries', ['timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_analysistimeseries_timestamp'), table_name='analysistimeseries')
    op.drop_index(op.f('ix_analysistimeseries_dataset_id'), table_name='analysistimeseries')
    op.drop_table('analysistimeseries')
