"""alter detector intercalibration table

Revision ID: 5481e97628c0
Revises: 4cf79de32004
Create Date: 2013-12-28 16:41:42.027252

"""

# revision identifiers, used by Alembic.
revision = '5481e97628c0'
down_revision = '4cf79de32004'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('proc_DetectorIntercalibrationTable','user_value', type_=sa.Float(32))
    op.alter_column('proc_DetectorIntercalibrationTable','user_error', type_=sa.Float(32))


def downgrade():
    pass
