"""update gen_usertable

Revision ID: 33af744196bc
Revises: 3816a8617056
Create Date: 2014-02-06 09:20:54.512707

"""

# revision identifiers, used by Alembic.
revision = '33af744196bc'
down_revision = '5975c80cd09d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('gen_UserTable', sa.Column('affiliation', sa.String(140)))
    op.add_column('gen_UserTable', sa.Column('category', sa.Integer))
    op.add_column('gen_UserTable', sa.Column('email', sa.String(140)))


def downgrade():
    op.drop_column('gen_UserTable', 'affiliation')
    op.drop_column('gen_UserTable', 'category')
    op.drop_column('gen_UserTable', 'email')
