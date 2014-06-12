"""added rocktype to sampletable

Revision ID: 30db613c85f8
Revises: 25d2a9d3371f
Create Date: 2014-06-11 22:14:57.055062

"""

# revision identifiers, used by Alembic.
revision = '30db613c85f8'
down_revision = '25d2a9d3371f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('gen_SampleTable', sa.Column('rock_type', sa.String(80)))


def downgrade():
    op.drop_column('gen_SampleTable', 'rock_type')
