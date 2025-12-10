"""add_collaborator_tables_all_modules

Revision ID: f2a43881a4ab
Revises: 7a4b5c6d7e8f
Create Date: 2025-12-10 15:40:18.252597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'f2a43881a4ab'
down_revision: Union[str, Sequence[str], None] = '7a4b5c6d7e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Add collaborator tables for all modules and owner_id to SSDProject."""
    # Add owner_id column to ssdproject if it doesn't exist
    if table_exists('ssdproject') and not column_exists('ssdproject', 'owner_id'):
        op.add_column('ssdproject', sa.Column('owner_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_ssdproject_owner', 'ssdproject', 'user', ['owner_id'], ['id'])
    
    # Create FSA project collaborator table
    if not table_exists('fsaprojectcollaborator'):
        op.create_table('fsaprojectcollaborator',
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['fsaproject.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('project_id', 'user_id')
        )
    
    # Create Verification project collaborator table
    if not table_exists('verificationprojectcollaborator'):
        op.create_table('verificationprojectcollaborator',
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['verificationproject.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('project_id', 'user_id')
        )
    
    # Create WQ (Water Quality) project collaborator table
    if not table_exists('wqprojectcollaborator'):
        op.create_table('wqprojectcollaborator',
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['waterqualityproject.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('project_id', 'user_id')
        )
    
    # Create SSD project collaborator table
    if not table_exists('ssdprojectcollaborator'):
        op.create_table('ssdprojectcollaborator',
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['ssdproject.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('project_id', 'user_id')
        )


def downgrade() -> None:
    """Remove collaborator tables."""
    if table_exists('ssdprojectcollaborator'):
        op.drop_table('ssdprojectcollaborator')
    if table_exists('wqprojectcollaborator'):
        op.drop_table('wqprojectcollaborator')
    if table_exists('verificationprojectcollaborator'):
        op.drop_table('verificationprojectcollaborator')
    if table_exists('fsaprojectcollaborator'):
        op.drop_table('fsaprojectcollaborator')
    
    # Remove owner_id from ssdproject
    if table_exists('ssdproject') and column_exists('ssdproject', 'owner_id'):
        op.drop_constraint('fk_ssdproject_owner', 'ssdproject', type_='foreignkey')
        op.drop_column('ssdproject', 'owner_id')
