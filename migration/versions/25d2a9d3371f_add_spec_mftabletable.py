"""add spec_MFTableTable

Revision ID: 25d2a9d3371f
Revises: 7ee6a4f68a6
Create Date: 2014-05-11 20:12:46.673495

"""

# revision identifiers, used by Alembic.
revision = '25d2a9d3371f'
down_revision = '7ee6a4f68a6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('spec_MFTableTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('create_date', sa.DateTime),
                    sa.Column('blob', sa.BLOB),
                    sa.Column('spectrometer_id',
                              sa.Integer,
                              sa.ForeignKey('gen_MassSpectrometerTable.id')))


def downgrade():
    op.drop_constraint(
        'spec_mftabletable_ibfk_1',
        'spec_MFTableTable',
        'foreignkey')
    op.drop_table('spec_MFTableTable')
