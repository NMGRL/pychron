"""update flux tables

Revision ID: 33aa8f82f642
Revises: 189f481fc3ed
Create Date: 2014-01-15 11:42:00.720417

"""

# revision identifiers, used by Alembic.
revision = '33aa8f82f642'
down_revision = '189f481fc3ed'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('flux_HistoryTable',sa.Column('create_date', sa.DateTime))
    op.add_column('flux_MonitorTable',sa.Column('ref', sa.String(140)))


def downgrade():
    op.drop_column('flux_HistoryTable', 'create_date')
    op.drop_column('flux_MonitorTable', 'ref')
