"""add reactor to irradiation

Revision ID: 3a183c5a512f
Revises: 591a97d42d42
Create Date: 2014-02-27 11:23:12.995322

"""

# revision identifiers, used by Alembic.
revision = '3a183c5a512f'
down_revision = '591a97d42d42'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('irrad_ReactorTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String(80)),
                    sa.Column('address', sa.String(180)),
                    sa.Column('reactor_type', sa.String(80)),
                    sa.Column('note', sa.BLOB))

    op.add_column('irrad_IrradiationTable',
                  sa.Column('reactor_id',
                            sa.Integer,
                            sa.ForeignKey('irrad_ReactorTable.id')))


def downgrade():
    op.drop_constraint('irrad_irradiationtable_ibfk_3', 'irrad_IrradiationTable', 'foreignkey')
    op.drop_column('irrad_IrradiationTable', 'reactor_id')
    op.drop_table('irrad_ReactorTable')
