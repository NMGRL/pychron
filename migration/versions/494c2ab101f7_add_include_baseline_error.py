"""add include_baseline_error

Revision ID: 494c2ab101f7
Revises: 3a183c5a512f
Create Date: 2014-03-04 10:21:44.752059

"""

# revision identifiers, used by Alembic.
revision = '494c2ab101f7'
down_revision = '3a183c5a512f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_FitTable', sa.Column('include_baseline_error',
                                             sa.Boolean))


def downgrade():
    op.drop_column('proc_FitTable', 'include_baseline_error')
