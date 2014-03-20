"""add eruptive environ to sample

Revision ID: 3d2790578104
Revises: 3b2ffebc124
Create Date: 2014-03-18 16:24:37.959594

"""

# revision identifiers, used by Alembic.
revision = '3d2790578104'
down_revision = '3b2ffebc124'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('gen_SampleTable', sa.Column('environment', sa.String(140)))


def downgrade():
    op.drop_column('gen_SampleTable', 'environment')
