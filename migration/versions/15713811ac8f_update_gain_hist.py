"""update gain hist

Revision ID: 15713811ac8f
Revises: 5064e5245149
Create Date: 2014-11-09 11:41:41.967873

"""

# revision identifiers, used by Alembic.
revision = '15713811ac8f'
down_revision = '5064e5245149'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('meas_GainHistoryTable',sa.Column('save_type', sa.String(20)))


def downgrade():
    op.drop_column('meas_GainHistoryTable', 'save_type')
