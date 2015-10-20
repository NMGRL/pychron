"""update gain table

Revision ID: 5064e5245149
Revises: 40dae38fbfe8
Create Date: 2014-11-04 20:01:09.588234

"""

# revision identifiers, used by Alembic.
revision = '5064e5245149'
down_revision = '40dae38fbfe8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('meas_GainHistoryTable',
                  sa.Column('applied_date',
                            sa.DateTime))


def downgrade():
    op.drop_column('meas_GainHistoryTable','applied_date')
