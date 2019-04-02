"""add unit to sampletbl

Revision ID: ed878002d0f3
Revises: 17a282d0e61e
Create Date: 2019-02-28 22:12:54.691791

"""

# revision identifiers, used by Alembic.
revision = 'ed878002d0f3'
down_revision = '17a282d0e61e'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('SampleTbl', sa.Column('unit', sa.String(80)))


def downgrade():
    op.drop_column('SampleTbl', 'unit')
