"""add to meas_ExtractionTable

Revision ID: 35a07261cd96
Revises: 2ca54f94d618
Create Date: 2013-11-17 16:59:28.024052

"""

# revision identifiers, used by Alembic.
revision = '35a07261cd96'
down_revision = '2ca54f94d618'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('meas_ExtractionTable',
                  sa.Column('beam_diameter', sa.Float))
    op.add_column('meas_ExtractionTable',
                  sa.Column('pattern', sa.String(100)))
    op.add_column('meas_ExtractionTable',
                  sa.Column('attenuator', sa.Float))
    op.add_column('meas_ExtractionTable',
                  sa.Column('mask_name', sa.String(100)))
    op.add_column('meas_ExtractionTable',
                  sa.Column('mask_position', sa.Float))
    op.add_column('meas_ExtractionTable',
                  sa.Column('ramp_rate', sa.Float))
    op.add_column('meas_ExtractionTable',
                  sa.Column('ramp_duration', sa.Float))
    op.add_column('meas_ExtractionTable',
                  sa.Column('reprate', sa.Float))


def downgrade():
    for ci in ('beam_diameter', 'pattern', 'attenuator', 'mask_name',
               'mask_position', 'ramp_rate', 'ramp_duration', 'reprate'):
        op.drop_column('meas_ExtractionTable', ci)
