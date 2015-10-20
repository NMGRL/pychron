"""add sample image

Revision ID: 2a77d61f4156
Revises: 502bd4123969
Create Date: 2015-01-15 09:45:56.915939

"""

# revision identifiers, used by Alembic.
revision = '2a77d61f4156'
down_revision = '502bd4123969'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import MEDIUMBLOB


def upgrade():
    op.create_table('med_SampleImageTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String(80)),
                    sa.Column('create_date', sa.TIMESTAMP),
                    sa.Column('image', MEDIUMBLOB),
                    sa.Column('note', sa.BLOB),
                    sa.Column('sample_id', sa.Integer, sa.ForeignKey('gen_SampleTable.id')))


def downgrade():
    op.drop_constraint(
        'med_sampleimagetable_ibfk_1',
        'med_SampleImageTable',
        'foreignkey')
    op.drop_table('med_SampleImageTable')
