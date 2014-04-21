"""add time_zero_offset to measurement table

Revision ID: 7ee6a4f68a6
Revises: 534de5290781
Create Date: 2014-04-21 15:19:45.040119

"""

# revision identifiers, used by Alembic.
revision = '7ee6a4f68a6'
down_revision = '534de5290781'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('meas_MeasurementTable', sa.Column('time_zero_offset', sa.Float))


def downgrade():
    op.drop_column('meas_MeasurementTable', 'time_zero_offset')
