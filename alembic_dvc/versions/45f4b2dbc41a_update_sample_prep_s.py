"""update sample prep steps

Revision ID: 45f4b2dbc41a
Revises: d1653e552ab
Create Date: 2018-07-18 10:01:26.668385

"""

# revision identifiers, used by Alembic.
revision = '45f4b2dbc41a'
down_revision = 'd1653e552ab'

import sqlalchemy as sa
from alembic import op


def upgrade():
    for step in ('mount', 'gold_table', 'us_wand', 'eds', 'cl', 'bse', 'se'):
        op.add_column('SamplePrepStepTbl',
                      sa.Column(step, sa.String(140)))


def downgrade():
    for step in ('mount', 'gold_table', 'us_wand', 'eds', 'cl', 'bse', 'se'):
        op.drop_column('SamplePrepStepTbl', step)
