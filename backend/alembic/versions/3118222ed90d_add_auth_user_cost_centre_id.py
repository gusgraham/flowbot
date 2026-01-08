"""add_auth_user_cost_centre_id

Revision ID: 3118222ed90d
Revises: 5f898d409b2c
Create Date: 2026-01-06 09:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3118222ed90d'
down_revision: Union[str, Sequence[str], None] = '5f898d409b2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cost_centre_id column to auth_user if it doesn't exist."""
    # Check if column already exists (to be safe)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('auth_user')]
    
    if 'cost_centre_id' not in columns:
        op.add_column('auth_user', sa.Column('cost_centre_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove cost_centre_id column from auth_user."""
    op.drop_column('auth_user', 'cost_centre_id')
