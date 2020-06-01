"""create_interpreted_table

Revision ID: 141cd61e4fb8
Revises: 4cefefc3ed78
Create Date: 2020-05-20 10:54:31.843058

"""

# revision identifiers, used by Alembic.
revision = '141cd61e4fb8'
down_revision = '4cefefc3ed78'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('InterpretedTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('sampleID', sa.Integer, sa.ForeignKey('SampleTbl.id')),
                    sa.Column('identifier', sa.String(40)),
                    sa.Column('create_date', sa.TIMESTAMP,
                              server_default=sa.text('CURRENT_TIMESTAMP')))

    op.create_table('InterpretedParameterTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('interpretedID', sa.Integer, sa.ForeignKey('InterpretedTbl.id')),
                    sa.Column('parameterID', sa.Integer, sa.ForeignKey('ParameterTbl.id')),
                    sa.Column('unitsID', sa.Integer, sa.ForeignKey('UnitsTbl.id')),
                    sa.Column('value', sa.Float(32)),
                    sa.Column('error', sa.Float(32)),
                    sa.Column('text', sa.BLOB))


def downgrade():
    op.drop_table('InterpretedParameterTbl')
    op.drop_table('InterpretedTbl')
