"""add sample prep choices

Revision ID: 3bda3115a662
Revises: 45f4b2dbc41a
Create Date: 2018-07-19 16:02:41.060054

"""

# revision identifiers, used by Alembic.
revision = '3bda3115a662'
down_revision = '45f4b2dbc41a'

import sqlalchemy as sa
from alembic import op


def upgrade():
    try:
        op.create_table('SamplePrepChoicesTbl',
                    sa.Column('id', sa.INTEGER, primary_key=True),
                    sa.Column('tag', sa.VARCHAR(140)),
                    sa.Column('value', sa.VARCHAR(140)),
                    )
    except sa.exc.InternalError:
        pass


def downgrade():
    op.drop_table('SamplePrepChoicesTbl')