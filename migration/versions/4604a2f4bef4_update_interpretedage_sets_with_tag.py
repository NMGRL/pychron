"""update interpretedage sets with tag

Revision ID: 4604a2f4bef4
Revises: 147ca17399a2
Create Date: 2014-03-27 09:01:15.868170

"""

# revision identifiers, used by Alembic.
revision = '4604a2f4bef4'
down_revision = '147ca17399a2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_InterpretedAgeSetTable', sa.Column('tag', sa.String(80)))


def downgrade():
    op.drop_column('proc_InterpretedAgeSetTable', 'tag')
