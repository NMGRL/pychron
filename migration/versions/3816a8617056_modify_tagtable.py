"""modify tagtable

Revision ID: 3816a8617056
Revises: 23d790125442
Create Date: 2014-01-25 13:37:15.645366

"""

# revision identifiers, used by Alembic.
revision = '3816a8617056'
down_revision = '23d790125442'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_TagTable',sa.Column('omit_series',sa.Boolean))


def downgrade():
    op.drop_column('proc_TagTable', 'omit_series')
