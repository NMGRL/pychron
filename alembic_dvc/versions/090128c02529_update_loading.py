"""update_loading

Revision ID: 090128c02529
Revises: 3bda3115a662
Create Date: 2018-10-03 16:10:06.831433

"""

# revision identifiers, used by Alembic.
revision = '090128c02529'
down_revision = '3bda3115a662'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('LoadPositionTbl',
                  sa.Column('nxtals', sa.Integer))


def downgrade():
    op.drop_column('LoadPositionTbl', 'nxtals')
