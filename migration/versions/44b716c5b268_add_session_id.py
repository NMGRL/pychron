"""add session_id

Revision ID: 44b716c5b268
Revises: 5bfd1830564
Create Date: 2014-09-19 01:18:42.290111

"""

# revision identifiers, used by Alembic.
revision = '44b716c5b268'
down_revision = '5bfd1830564'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_BlanksHistoryTable', sa.Column('session', sa.String(40)))
    op.add_column('proc_FitHistoryTable', sa.Column('session', sa.String(40)))

def downgrade():
    op.drop_column('proc_BlanksHistoryTable','session')
    op.drop_column('proc_FitHistoryTable','session')
