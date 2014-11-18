"""add tas to sample table

Revision ID: 3b2ffebc124
Revises: 494c2ab101f7
Create Date: 2014-03-13 12:00:13.350200

"""

# revision identifiers, used by Alembic.
revision = '3b2ffebc124'
down_revision = '494c2ab101f7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('gen_SampleTable', sa.Column('sio2', sa.Float(32)))
    op.add_column('gen_SampleTable', sa.Column('k2o', sa.Float(32)))
    op.add_column('gen_SampleTable', sa.Column('na2o', sa.Float(32)))


def downgrade():
    op.drop_column('gen_SampleTable', 'sio2')
    op.drop_column('gen_SampleTable', 'k2o')
    op.drop_column('gen_SampleTable', 'na2o')
