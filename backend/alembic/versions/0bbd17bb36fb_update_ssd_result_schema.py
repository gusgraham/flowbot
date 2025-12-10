"""update_ssd_result_schema

Revision ID: 0bbd17bb36fb
Revises: b0bcce7e4ac5
Create Date: 2025-12-09 21:32:27.377424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0bbd17bb36fb'
down_revision: Union[str, Sequence[str], None] = 'b0bcce7e4ac5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade SSDResult table with new columns for comprehensive analysis results."""
    # Add new columns to ssdresult table
    with op.batch_alter_table('ssdresult', schema=None) as batch_op:
        # Add scenario_id foreign key
        batch_op.add_column(sa.Column('scenario_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_ssdresult_scenario', 'analysisscenario', ['scenario_id'], ['id'])
        
        # Add snapshot columns for result history
        batch_op.add_column(sa.Column('scenario_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('config_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('spill_target', sa.Integer(), nullable=True))
        
        # Add analysis metrics columns
        batch_op.add_column(sa.Column('converged', sa.Boolean(), nullable=True, server_default=sa.text('1')))
        batch_op.add_column(sa.Column('iterations', sa.Integer(), nullable=True, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('bathing_spill_volume_m3', sa.Float(), nullable=True, server_default=sa.text('0.0')))
        batch_op.add_column(sa.Column('total_spill_duration_hours', sa.Float(), nullable=True, server_default=sa.text('0.0')))
        
        # Add spill events JSON column
        batch_op.add_column(sa.Column('spill_events', sa.JSON(), nullable=True))
        
        # Add timeseries path column (replaces result_artifact_path)
        batch_op.add_column(sa.Column('timeseries_path', sa.String(), nullable=True))
        
        # Drop old result_artifact_path column if it exists
        try:
            batch_op.drop_column('result_artifact_path')
        except Exception:
            pass  # Column may not exist


def downgrade() -> None:
    """Downgrade - remove the new columns."""
    with op.batch_alter_table('ssdresult', schema=None) as batch_op:
        # Drop new columns
        batch_op.drop_column('timeseries_path')
        batch_op.drop_column('spill_events')
        batch_op.drop_column('total_spill_duration_hours')
        batch_op.drop_column('bathing_spill_volume_m3')
        batch_op.drop_column('iterations')
        batch_op.drop_column('converged')
        batch_op.drop_column('spill_target')
        batch_op.drop_column('config_name')
        batch_op.drop_column('scenario_name')
        batch_op.drop_constraint('fk_ssdresult_scenario', type_='foreignkey')
        batch_op.drop_column('scenario_id')
        
        # Re-add result_artifact_path
        batch_op.add_column(sa.Column('result_artifact_path', sa.String(), nullable=False))
