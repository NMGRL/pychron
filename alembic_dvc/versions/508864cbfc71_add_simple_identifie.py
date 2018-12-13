"""add simple_identifier

Revision ID: 508864cbfc71
Revises: 35388de3b2c1
Create Date: 2017-04-21 08:16:09.841511

"""

# revision identifiers, used by Alembic.
revision = '508864cbfc71'
down_revision = '35388de3b2c1'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('SimpleIdentifierTbl',
                    sa.Column('identifier', sa.Integer(), primary_key=True),
                    sa.Column('sampleID', sa.Integer(), sa.ForeignKey('SampleTbl.id')))

    op.add_column('AnalysisTbl',
                  sa.Column('simple_identifier', sa.Integer(), sa.ForeignKey('SimpleIdentifierTbl.identifier')))


def downgrade():
    op.drop_column('AnalysisTbl', 'simple_identifier')
    op.drop_table('SimpleIdentifierTbl')
