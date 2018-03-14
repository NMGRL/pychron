"""sample prep updates

Revision ID: 69484796482
Revises: 35388de3b2c1
Create Date: 2018-02-26 15:56:36.885264

"""

# revision identifiers, used by Alembic.
import datetime

from sqlalchemy import func

revision = '69484796482'
down_revision = '508864cbfc71'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('SampleTbl',
                  sa.Column('storage_location', sa.String(140)))

    op.add_column('SampleTbl',
                  sa.Column('lithology', sa.String(140)))

    op.add_column('SampleTbl',
                  sa.Column('location', sa.String(140)))

    op.add_column('SampleTbl',
                  sa.Column('approximate_age', sa.Float))

    op.add_column('SampleTbl',
                  sa.Column('elevation', sa.Float))

    op.add_column('SampleTbl',
                  sa.Column('create_date', sa.DateTime))

    op.add_column('SampleTbl',
                  sa.Column('update_date', sa.DateTime))


def downgrade():
    op.drop_column('SampleTbl', 'storage_location')
    op.drop_column('SampleTbl', 'lithology')
    op.drop_column('SampleTbl', 'approximate_age')
    op.drop_column('SampleTbl', 'elevation')
    op.drop_column('SampleTbl', 'create_date')
    op.drop_column('SampleTbl', 'location')
    op.drop_column('SampleTbl', 'update_date')

