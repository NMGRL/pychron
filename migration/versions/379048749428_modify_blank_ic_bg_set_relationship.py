"""modify blank/ic/bg-set relationship

Revision ID: 379048749428
Revises: 33aa8f82f642
Create Date: 2014-01-24 17:23:54.748266

"""

# revision identifiers, used by Alembic.
revision = '379048749428'
down_revision = '33aa8f82f642'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_DetectorIntercalibrationSetTable',
                  sa.Column('set_id',sa.Integer))
    op.add_column('proc_BlanksSetTable',
                  sa.Column('set_id', sa.Integer))
    op.add_column('proc_BackgroundsSetTable',
                  sa.Column('set_id', sa.Integer))

    op.add_column('proc_DetectorIntercalibrationTable',
                  sa.Column('set_id', sa.Integer))
    op.add_column('proc_BlanksTable',
              sa.Column('set_id', sa.Integer))
    op.add_column('proc_BackgroundsTable',
              sa.Column('set_id', sa.Integer))

    op.add_column('proc_DetectorIntercalibrationTable',
                  sa.Column('error_type', sa.String(40)))
    op.add_column('proc_BlanksTable',
                  sa.Column('error_type', sa.String(40)))
    op.add_column('proc_BackgroundsTable',
                  sa.Column('error_type', sa.String(40)))

def downgrade():
    op.drop_column('proc_DetectorIntercalibrationSetTable','set_id')
    op.drop_column('proc_BlanksSetTable','set_id')
    op.drop_column('proc_BackgroundsSetTable','set_id')

    op.drop_column('proc_DetectorIntercalibrationTable', 'set_id')
    op.drop_column('proc_BlanksTable', 'set_id')
    op.drop_column('proc_BackgroundsTable', 'set_id')

    op.drop_column('proc_DetectorIntercalibrationTable', 'error_type')
    op.drop_column('proc_BlanksTable', 'error_type')
    op.drop_column('proc_BackgroundsTable', 'error_type')
