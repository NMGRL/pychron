"""add media tbl

Revision ID: 35388de3b2c1
Revises: 505762cf10ed
Create Date: 2016-10-21 20:10:09.234907

"""

# revision identifiers, used by Alembic.
revision = '35388de3b2c1'
down_revision = '505762cf10ed'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('MediaTbl',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('analysisID', sa.Integer, sa.ForeignKey('AnalysisTbl.id')),
                    sa.Column('username', sa.String(140), sa.ForeignKey('UserTbl.name')),
                    sa.Column('url', sa.TEXT),
                    sa.Column('create_date', sa.TIMESTAMP))


def downgrade():
    op.drop_table('MediaTbl')
