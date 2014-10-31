"""update load table

Revision ID: 37edda381f28
Revises: 646ef1d2793
Create Date: 2014-10-31 00:44:04.121875

"""

# revision identifiers, used by Alembic.
revision = '37edda381f28'
down_revision = '646ef1d2793'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('loading_LoadTable',
                  sa.Column('archived', sa.Boolean))


def downgrade():
    op.drop_column('loading_LoadTable','archived')
