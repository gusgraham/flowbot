"""add_spill_target_bathing_to_ssdresult

Revision ID: 7a4b5c6d7e8f
Revises: 6383a8b23f1e
Create Date: 2025-12-10 12:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a4b5c6d7e8f'
down_revision = '6383a8b23f1e'
branch_labels = None
depends_on = None


def upgrade():
    # Add spill_target_bathing column to ssdresult table
    op.add_column('ssdresult', sa.Column('spill_target_bathing', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('ssdresult', 'spill_target_bathing')
