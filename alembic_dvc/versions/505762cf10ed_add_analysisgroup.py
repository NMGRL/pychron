"""add analysisgroup

Revision ID: 505762cf10ed
Revises: 9909cbd2e8e
Create Date: 2016-07-15 12:28:17.389147

"""

# revision identifiers, used by Alembic.
revision = '505762cf10ed'
down_revision = '9909cbd2e8e'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('AnalysisGroupTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String(140)),
                    sa.Column('create_date', sa.TIMESTAMP),
                    sa.Column('projectID', sa.Integer, sa.ForeignKey('ProjectTbl.id')),
                    sa.Column('user', sa.String(140), sa.ForeignKey('UserTbl.name')))

    op.create_table('AnalysisGroupSetTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('analysisID', sa.Integer, sa.ForeignKey('AnalysisTbl.id')),
                    sa.Column('groupID', sa.Integer, sa.ForeignKey('AnalysisGroupTbl.id')))


def downgrade():
    op.drop_table('AnalysisGroupSetTbl')
    op.drop_table('AnalysisGroupTbl')
