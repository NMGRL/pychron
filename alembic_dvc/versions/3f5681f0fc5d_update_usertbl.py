"""update usertbl

Revision ID: 3f5681f0fc5d
Revises: 50066dd5c568
Create Date: 2015-06-03 07:33:00.802336

"""

# revision identifiers, used by Alembic.
revision = '3f5681f0fc5d'
down_revision = '50066dd5c568'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('UserTbl',
                  sa.Column('affiliation', sa.String(80)))

    op.add_column('UserTbl',
                  sa.Column('category', sa.String(80)))

    op.add_column('UserTbl',
                  sa.Column('email', sa.String(80)))


def downgrade():
    op.drop_column('UserTbl', 'affiliation')

    op.drop_column('UserTbl', 'category')

    op.drop_column('UserTbl', 'email')
