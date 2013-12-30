"""alter interpreted age set table

Revision ID: b5443ca152f
Revises: 5481e97628c0
Create Date: 2013-12-30 13:24:51.766347

"""

# revision identifiers, used by Alembic.
revision = 'b5443ca152f'
down_revision = '5481e97628c0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_InterpretedAgeSetTable', sa.Column('plateau_step', sa.Boolean))


def downgrade():
    op.drop_column('proc_InterpretedAgeSetTable', 'plateau_step')
