"""add RestrictedNameTbl

Revision ID: 1ca68590acc1
Revises: 4e1a5a724f61
Create Date: 2016-05-18 10:52:28.807242

"""

# revision identifiers, used by Alembic.
revision = '1ca68590acc1'
down_revision = '4e1a5a724f61'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('RestrictedNameTbl',
                    sa.Column('id', sa.INT, primary_key=True),
                    sa.Column('name', sa.String(40)),
                    sa.Column('category', sa.String(40)))


def downgrade():
    op.drop_table('RestrictedNameTbl')
