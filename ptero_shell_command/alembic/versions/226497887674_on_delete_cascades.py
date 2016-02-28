"""on_delete_cascades

Revision ID: 226497887674
Revises: 1ccbd657f3b5
Create Date: 2016-02-28 03:46:57.056699

"""

# revision identifiers, used by Alembic.
revision = '226497887674'
down_revision = '1ccbd657f3b5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint(u'fk_job_status_history_job_id_job', 'job_status_history', type_='foreignkey')
    op.create_foreign_key(op.f('fk_job_status_history_job_id_job'), 'job_status_history', 'job', ['job_id'], ['id'], ondelete='CASCADE')


def downgrade():
    op.drop_constraint(op.f('fk_job_status_history_job_id_job'), 'job_status_history', type_='foreignkey')
    op.create_foreign_key(u'fk_job_status_history_job_id_job', 'job_status_history', 'job', ['job_id'], ['id'])

# flake8: noqa
