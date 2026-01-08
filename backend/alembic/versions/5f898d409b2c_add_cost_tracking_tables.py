"""add_cost_tracking_tables

Revision ID: 5f898d409b2c
Revises: 4d952e1a0afb
Create Date: 2026-01-06 09:24:11.297499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f898d409b2c'
down_revision: Union[str, Sequence[str], None] = '4d952e1a0afb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cost tracking tables and add cost_centre_id to auth_user."""
    
    # 1. Create admin_cost_centre table FIRST (before auth_user FK)
    op.create_table(
        'admin_cost_centre',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('code', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # 2. Add cost_centre_id to auth_user
    op.add_column('auth_user', sa.Column('cost_centre_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_auth_user_cost_centre',
        'auth_user', 'admin_cost_centre',
        ['cost_centre_id'], ['id']
    )
    
    # 3. Create admin_module_weight table
    op.create_table(
        'admin_module_weight',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('module', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('weight', sa.Float(), nullable=False, default=1.0),
        sa.Column('description', sa.String(), nullable=True),
    )
    
    # 4. Create admin_usage_log table
    op.create_table(
        'admin_usage_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('auth_user.id'), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('module', sa.String(), nullable=False, index=True),
        sa.Column('weight', sa.Float(), nullable=False, default=1.0),
    )
    
    # 5. Create admin_storage_snapshot table
    op.create_table(
        'admin_storage_snapshot',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('auth_user.id'), nullable=False, index=True),
        sa.Column('project_id', sa.Integer(), nullable=False, index=True),
        sa.Column('module', sa.String(), nullable=False, index=True),
        sa.Column('snapshot_date', sa.Date(), nullable=False, index=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False, default=0),
    )
    
    # 6. Create admin_budget_config table
    op.create_table(
        'admin_budget_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('hosting_budget', sa.Float(), nullable=False),
        sa.Column('development_budget', sa.Float(), nullable=False),
        sa.Column('storage_weight_pct', sa.Integer(), nullable=False, default=30),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # 7. Create admin_monthly_invoice table
    op.create_table(
        'admin_monthly_invoice',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cost_centre_id', sa.Integer(), sa.ForeignKey('admin_cost_centre.id'), nullable=False, index=True),
        sa.Column('year_month', sa.String(), nullable=False, index=True),
        sa.Column('total_budget', sa.Float(), nullable=False),
        sa.Column('share_pct', sa.Float(), nullable=False),
        sa.Column('utilization_cost', sa.Float(), nullable=False),
        sa.Column('storage_cost', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('details_json', sa.String(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
    )
    
    # 8. Seed default module weights
    op.execute("""
        INSERT INTO admin_module_weight (module, weight, description) VALUES
        ('FSM', 1.0, 'Flow Survey Management'),
        ('FSA', 1.0, 'Flow Survey Analysis'),
        ('WQ', 1.0, 'Water Quality'),
        ('VER', 1.0, 'Verification'),
        ('SSD', 1.0, 'Spill Storage Design')
    """)


def downgrade() -> None:
    """Remove cost tracking tables."""
    op.drop_table('admin_monthly_invoice')
    op.drop_table('admin_budget_config')
    op.drop_table('admin_storage_snapshot')
    op.drop_table('admin_usage_log')
    op.drop_table('admin_module_weight')
    op.drop_constraint('fk_auth_user_cost_centre', 'auth_user', type_='foreignkey')
    op.drop_column('auth_user', 'cost_centre_id')
    op.drop_table('admin_cost_centre')
