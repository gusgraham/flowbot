"""add verification module tables

Revision ID: 1a2b3c4d5e6f
Revises: f2a43881a4ab
Create Date: 2024-12-11 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = 'f2a43881a4ab'
branch_labels = None
depends_on = None


def upgrade():
    # Helper to check if table exists (for SQLite)
    conn = op.get_bind()
    
    def table_exists(name):
        result = conn.execute(sa.text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'"))
        return result.fetchone() is not None
    
    def index_exists(name):
        result = conn.execute(sa.text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{name}'"))
        return result.fetchone() is not None

    # VerificationEvent table
    if not table_exists('verificationevent'):
        op.create_table(
            'verificationevent',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('event_type', sa.String(), nullable=False, server_default='STORM'),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('start_time', sa.DateTime(), nullable=True),
            sa.Column('end_time', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['verificationproject.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_verificationevent_name'):
        op.create_index('ix_verificationevent_name', 'verificationevent', ['name'])
    if not index_exists('ix_verificationevent_project_id'):
        op.create_index('ix_verificationevent_project_id', 'verificationevent', ['project_id'])

    # VerificationFlowMonitor table
    if not table_exists('verificationflowmonitor'):
        op.create_table(
            'verificationflowmonitor',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('icm_node_reference', sa.String(), nullable=True),
            sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('is_surcharged', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['verificationproject.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_verificationflowmonitor_name'):
        op.create_index('ix_verificationflowmonitor_name', 'verificationflowmonitor', ['name'])
    if not index_exists('ix_verificationflowmonitor_project_id'):
        op.create_index('ix_verificationflowmonitor_project_id', 'verificationflowmonitor', ['project_id'])

    # TraceSet table
    if not table_exists('traceset'):
        op.create_table(
            'traceset',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('source_file', sa.String(), nullable=True),
            sa.Column('imported_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['event_id'], ['verificationevent.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_traceset_name'):
        op.create_index('ix_traceset_name', 'traceset', ['name'])
    if not index_exists('ix_traceset_event_id'):
        op.create_index('ix_traceset_event_id', 'traceset', ['event_id'])

    # MonitorTraceVersion table
    if not table_exists('monitortraceversion'):
        op.create_table(
            'monitortraceversion',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('trace_set_id', sa.Integer(), nullable=False),
            sa.Column('monitor_id', sa.Integer(), nullable=False),
            sa.Column('timestep_minutes', sa.Integer(), nullable=False, server_default='2'),
            sa.Column('upstream_end', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('obs_location_name', sa.String(), nullable=True),
            sa.Column('pred_location_name', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['trace_set_id'], ['traceset.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['monitor_id'], ['verificationflowmonitor.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_monitortraceversion_trace_set_id'):
        op.create_index('ix_monitortraceversion_trace_set_id', 'monitortraceversion', ['trace_set_id'])
    if not index_exists('ix_monitortraceversion_monitor_id'):
        op.create_index('ix_monitortraceversion_monitor_id', 'monitortraceversion', ['monitor_id'])

    # VerificationTimeSeries table
    if not table_exists('verificationtimeseries'):
        op.create_table(
            'verificationtimeseries',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('monitor_trace_id', sa.Integer(), nullable=False),
            sa.Column('series_type', sa.String(), nullable=False),
            sa.Column('parquet_path', sa.String(), nullable=False),
            sa.Column('start_time', sa.DateTime(), nullable=True),
            sa.Column('end_time', sa.DateTime(), nullable=True),
            sa.Column('record_count', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['monitor_trace_id'], ['monitortraceversion.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_verificationtimeseries_monitor_trace_id'):
        op.create_index('ix_verificationtimeseries_monitor_trace_id', 'verificationtimeseries', ['monitor_trace_id'])

    # ToleranceSet table
    if not table_exists('toleranceset'):
        op.create_table(
            'toleranceset',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('event_type', sa.String(), nullable=False, server_default='STORM'),
            sa.Column('for_critical', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('for_surcharged', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('depth_time_tolerance_hrs', sa.Float(), nullable=False, server_default='0.5'),
            sa.Column('depth_peak_tolerance_pct', sa.Float(), nullable=False, server_default='10.0'),
            sa.Column('depth_peak_tolerance_abs_m', sa.Float(), nullable=False, server_default='0.1'),
            sa.Column('depth_peak_surcharged_upper_m', sa.Float(), nullable=False, server_default='0.5'),
            sa.Column('depth_peak_surcharged_lower_m', sa.Float(), nullable=False, server_default='0.1'),
            sa.Column('flow_nse_threshold', sa.Float(), nullable=False, server_default='0.5'),
            sa.Column('flow_time_tolerance_hrs', sa.Float(), nullable=False, server_default='0.5'),
            sa.Column('flow_peak_tolerance_upper_pct', sa.Float(), nullable=False, server_default='25.0'),
            sa.Column('flow_peak_tolerance_lower_pct', sa.Float(), nullable=False, server_default='15.0'),
            sa.Column('flow_volume_tolerance_upper_pct', sa.Float(), nullable=False, server_default='20.0'),
            sa.Column('flow_volume_tolerance_lower_pct', sa.Float(), nullable=False, server_default='10.0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['verificationproject.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_toleranceset_name'):
        op.create_index('ix_toleranceset_name', 'toleranceset', ['name'])
    if not index_exists('ix_toleranceset_project_id'):
        op.create_index('ix_toleranceset_project_id', 'toleranceset', ['project_id'])

    # VerificationRun table
    if not table_exists('verificationrun'):
        op.create_table(
            'verificationrun',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('monitor_trace_id', sa.Integer(), nullable=False),
            sa.Column('tolerance_set_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
            sa.Column('is_final_for_monitor_event', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('overall_flow_score', sa.Float(), nullable=True),
            sa.Column('overall_depth_score', sa.Float(), nullable=True),
            sa.Column('overall_status', sa.String(), nullable=True),
            sa.Column('nse', sa.Float(), nullable=True),
            sa.Column('kge', sa.Float(), nullable=True),
            sa.Column('cv_obs', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('finalized_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['monitor_trace_id'], ['monitortraceversion.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tolerance_set_id'], ['toleranceset.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_verificationrun_monitor_trace_id'):
        op.create_index('ix_verificationrun_monitor_trace_id', 'verificationrun', ['monitor_trace_id'])

    # VerificationMetric table
    if not table_exists('verificationmetric'):
        op.create_table(
            'verificationmetric',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('run_id', sa.Integer(), nullable=False),
            sa.Column('parameter', sa.String(), nullable=False),
            sa.Column('metric_name', sa.String(), nullable=False),
            sa.Column('value', sa.Float(), nullable=False),
            sa.Column('score_band', sa.String(), nullable=True),
            sa.Column('score_points', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['run_id'], ['verificationrun.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_verificationmetric_run_id'):
        op.create_index('ix_verificationmetric_run_id', 'verificationmetric', ['run_id'])

    # ManualAdjustment table
    if not table_exists('manualadjustment'):
        op.create_table(
            'manualadjustment',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('run_id', sa.Integer(), nullable=False),
            sa.Column('adjustment_type', sa.String(), nullable=False),
            sa.Column('parameter', sa.String(), nullable=False),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('reason', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['run_id'], ['verificationrun.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('ix_manualadjustment_run_id'):
        op.create_index('ix_manualadjustment_run_id', 'manualadjustment', ['run_id'])


def downgrade():
    # Helper to check if table exists (for SQLite)
    conn = op.get_bind()
    
    def table_exists(name):
        result = conn.execute(sa.text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'"))
        return result.fetchone() is not None
    
    if table_exists('manualadjustment'):
        op.drop_table('manualadjustment')
    if table_exists('verificationmetric'):
        op.drop_table('verificationmetric')
    if table_exists('verificationrun'):
        op.drop_table('verificationrun')
    if table_exists('toleranceset'):
        op.drop_table('toleranceset')
    if table_exists('verificationtimeseries'):
        op.drop_table('verificationtimeseries')
    if table_exists('monitortraceversion'):
        op.drop_table('monitortraceversion')
    if table_exists('traceset'):
        op.drop_table('traceset')
    if table_exists('verificationflowmonitor'):
        op.drop_table('verificationflowmonitor')
    if table_exists('verificationevent'):
        op.drop_table('verificationevent')
