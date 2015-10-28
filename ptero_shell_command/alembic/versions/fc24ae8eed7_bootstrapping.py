"""bootstrapping

Revision ID: fc24ae8eed7
Revises: 
Create Date: 2015-10-23 21:18:08.413688

"""

# revision identifiers, used by Alembic.
revision = 'fc24ae8eed7'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('job',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('command_line', postgresql.JSON(), nullable=False),
        sa.Column('working_directory', sa.Text(), nullable=False),
        sa.Column('environment', postgresql.JSON(), nullable=True),
        sa.Column('stdin', sa.Text(), nullable=True),
        sa.Column('umask', sa.Integer(), nullable=True),
        sa.Column('user', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('webhooks', postgresql.JSON(), nullable=False),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.Column('exit_code', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_job'))
    )
    op.create_index(op.f('ix_job_status'), 'job', ['status'], unique=False)
    op.create_index(op.f('ix_job_user'), 'job', ['user'], unique=False)
    op.create_table('job_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', postgresql.UUID(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], [u'job.id'], name=op.f('fk_job_status_history_job_id_job')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_job_status_history'))
    )
    op.create_index(op.f('ix_job_status_history_job_id'), 'job_status_history', ['job_id'], unique=False)
    op.create_index(op.f('ix_job_status_history_status'), 'job_status_history', ['status'], unique=False)


def downgrade():
    raise NotImplementedError("Cannot reverse bootstrapping")

# flake8: noqa
