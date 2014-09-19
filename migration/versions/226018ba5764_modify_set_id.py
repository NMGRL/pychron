"""modify set_id

Revision ID: 226018ba5764
Revises: 2fef0dd027ad
Create Date: 2014-09-19 10:31:36.390461

"""

# revision identifiers, used by Alembic.
revision = '226018ba5764'
down_revision = '2fef0dd027ad'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('proc_BlanksTable','set_id',
                    type_=sa.String(40),
                    existing_type=sa.BIGINT)
    op.alter_column('proc_BlanksSetTable','set_id',
                    type_=sa.String(40),
                    existing_type=sa.BIGINT)

    op.alter_column('proc_BackgroundsTable','set_id',
                    type_=sa.String(40),
                    existing_type=sa.INTEGER)
    op.alter_column('proc_BackgroundsSetTable','set_id',
                    type_=sa.String(40),
                    existing_type=sa.INTEGER)

    op.alter_column('proc_DetectorIntercalibrationTable','set_id',
                    type_=sa.String(40),
                    existing_type=sa.INTEGER)
    op.alter_column('proc_DetectorIntercalibrationSetTable','set_id',
                    type_=sa.String(40),
                    existing_type=sa.INTEGER)

def downgrade():
    op.alter_column('proc_BlanksTable', 'set_id',
                    type_=sa.BIGINT,
                    existing_type=sa.String(40))
    op.alter_column('proc_BlanksSetTable', 'set_id',
                    type_=sa.BIGINT,
                    existing_type=sa.String(40))

    op.alter_column('proc_BackgroundsTable','set_id',
                    type_=sa.INTEGER,
                    existing_type=sa.String(40))
    op.alter_column('proc_BackgroundsSetTable','set_id',
                    type_=sa.INTEGER,
                    existing_type=sa.String(40))

    op.alter_column('proc_DetectorIntercalibrationTable','set_id',
                    type_=sa.INTEGER,
                    existing_type=sa.String(40))
    op.alter_column('proc_DetectorIntercalibrationSetTable','set_id',
                    type_=sa.INTEGER,
                    existing_type=sa.String(40))
