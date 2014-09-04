"""update irrad_production

Revision ID: 4ab75910bd34
Revises: 9b63a03f7ee
Create Date: 2014-09-04 10:41:18.508275

"""

# revision identifiers, used by Alembic.
revision = '4ab75910bd34'
down_revision = '9b63a03f7ee'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('irrad_ProductionTable', sa.Column('note', sa.BLOB))
    op.add_column('irrad_ProductionTable', sa.Column('last_modified', sa.DateTime))


def downgrade():
    op.drop_column('irrad_ProductionTable', 'note')
    op.drop_column('irrad_ProductionTable', 'last_modified')
