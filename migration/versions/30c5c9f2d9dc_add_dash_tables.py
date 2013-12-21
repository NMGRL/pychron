"""add dash tables

Revision ID: 30c5c9f2d9dc
Revises: 38fc7371a444
Create Date: 2013-12-20 14:39:54.479895

"""

# revision identifiers, used by Alembic.
revision = '30c5c9f2d9dc'
down_revision = '38fc7371a444'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('dash_TimeTable',
                    sa.Column('start', sa.DateTime),
                    sa.Column('end', sa.DateTime),
                    sa.Column('id', sa.Integer, primary_key=True))
    op.create_table('dash_DeviceTable',
                    sa.Column('name', sa.String(80)),
                    sa.Column('scan_fmt', sa.String(32)),
                    sa.Column('scan_meta', sa.BLOB),
                    sa.Column('scan_blob', sa.BLOB),
                    sa.Column('time_table_id', sa.Integer),
                    sa.Column('id', sa.Integer, primary_key=True))


def downgrade():
    op.drop_table('dash_TimeTable')
    op.drop_table('dash_DeviceTable')
