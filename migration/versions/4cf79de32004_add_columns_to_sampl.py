"""add columns to sampletable

Revision ID: 4cf79de32004
Revises: 4a5e23eb4fae
Create Date: 2013-12-23 09:05:11.647750

"""

# revision identifiers, used by Alembic.
revision = '4cf79de32004'
down_revision = '4a5e23eb4fae'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('gen_SampleTable',sa.Column('location',sa.String(80)))
    op.add_column('gen_SampleTable',sa.Column('lat', sa.Float(32)))
    op.add_column('gen_SampleTable',sa.Column('long', sa.Float(32)))
    op.add_column('gen_SampleTable',sa.Column('elevation',sa.Float))
    op.add_column('gen_SampleTable',sa.Column('igsn',sa.CHAR(9)))
    op.add_column('gen_SampleTable',sa.Column('note',sa.BLOB))
    op.add_column('gen_SampleTable',sa.Column('lithology',sa.String(80)))
    op.add_column('gen_SampleTable',sa.Column('alt_name',sa.String(80)))


def downgrade():
    op.drop_column('gen_SampleTable', 'location')
    op.drop_column('gen_SampleTable', 'lat')
    op.drop_column('gen_SampleTable', 'long')
    op.drop_column('gen_SampleTable', 'elevation')
    op.drop_column('gen_SampleTable', 'igsn')
    op.drop_column('gen_SampleTable', 'note')
    op.drop_column('gen_SampleTable', 'lithology')
    op.drop_column('gen_SampleTable', 'alt_name')
