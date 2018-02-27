"""sample prep updates

Revision ID: 69484796482
Revises: 35388de3b2c1
Create Date: 2018-02-26 15:56:36.885264

"""

# revision identifiers, used by Alembic.
revision = '69484796482'
down_revision = '508864cbfc71'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('SampleTbl',
                  sa.Column('storage_location', sa.String(140)))

    op.add_column('SampleTbl',
                  sa.Column('lithology', sa.String(140)))


def downgrade():
    op.drop_column('SampleTbl', 'storage_location')
    op.drop_column('SampleTbl', 'lithology')
