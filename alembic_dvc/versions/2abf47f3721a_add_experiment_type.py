"""add experiment_type

Revision ID: 2abf47f3721a
Revises: 69484796482
Create Date: 2018-04-09 09:46:00.107024

"""

# revision identifiers, used by Alembic.
revision = '2abf47f3721a'
down_revision = '69484796482'

import sqlalchemy as sa
from alembic import op


def upgrade():
    try:
        op.add_column('AnalysisTbl',
                  sa.Column('experiment_type', sa.String(32)))
    except sa.exc.InternalError:
        pass

def downgrade():
    op.drop_column('AnalysisTbl', 'experiment_type')
