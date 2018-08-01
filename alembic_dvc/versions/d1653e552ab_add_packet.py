"""add packet

Revision ID: d1653e552ab
Revises: 2abf47f3721a
Create Date: 2018-07-18 09:59:42.347777

"""

# revision identifiers, used by Alembic.
revision = 'd1653e552ab'
down_revision = '2abf47f3721a'

import sqlalchemy as sa
from alembic import op


def upgrade():
    try:

        op.add_column('IrradiationPositionTbl',
                      sa.Column('packet', sa.String(32)))

    except BaseException:
        pass


def downgrade():
    op.drop_column('IrradiationPositionTbl', 'packet')