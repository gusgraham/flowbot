"""add fsa_dwf_monitor_settings table

Revision ID: 26a307ca4ed9
Revises: 26a7fca76299
Create Date: 2026-02-02 09:24:48.530840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26a307ca4ed9'
down_revision: Union[str, Sequence[str], None] = '26a7fca76299'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('fsa_dwf_monitor_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('sg_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sg_window', sa.Integer(), nullable=False, server_default='21'),
        sa.Column('sg_order', sa.Integer(), nullable=False, server_default='3'),
        sa.ForeignKeyConstraint(['dataset_id'], ['fsa_dataset.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fsa_dwf_monitor_settings_dataset_id'), 'fsa_dwf_monitor_settings', ['dataset_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_fsa_dwf_monitor_settings_dataset_id'), table_name='fsa_dwf_monitor_settings')
    op.drop_table('fsa_dwf_monitor_settings')
