"""retry

Revision ID: 1ccbd657f3b5
Revises: fc24ae8eed7
Create Date: 2015-12-13 05:02:01.157181

"""

# revision identifiers, used by Alembic.
revision = '1ccbd657f3b5'
down_revision = 'fc24ae8eed7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('job', sa.Column('retry_settings', postgresql.JSON(), nullable=True))


def downgrade():
    op.drop_column('job', 'retry_settings')

# flake8: noqa
