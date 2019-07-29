"""add currenttbl

Revision ID: 7497821c0290
Revises: ed878002d0f3
Create Date: 2019-07-24 16:25:03.095429

"""

# revision identifiers, used by Alembic.
revision = '7497821c0290'
down_revision = 'ed878002d0f3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('ParameterTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String(40)))
    op.create_table('UnitsTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String(40)))

    op.create_table('CurrentTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('timestamp', sa.TIMESTAMP,
                              server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
                    sa.Column('parameterID', sa.Integer, sa.ForeignKey('ParameterTbl.id')),
                    sa.Column('analysisID', sa.Integer, sa.ForeignKey('AnalysisTbl.id')),
                    sa.Column('unitID', sa.Integer, sa.ForeignKey('UnitsTbl.id')),
                    sa.Column('value', sa.Float(32)),
                    sa.Column('error', sa.Float(32)))


def downgrade():
    op.drop_table('CurrentTbl')
    op.drop_table('ParameterTbl')
    op.drop_table('UnitsTbl')
