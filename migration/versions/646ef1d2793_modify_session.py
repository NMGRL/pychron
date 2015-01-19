"""modify session

Revision ID: 646ef1d2793
Revises: 226018ba5764
Create Date: 2014-09-19 11:31:56.171492

"""

# revision identifiers, used by Alembic.
revision = '646ef1d2793'
down_revision = '226018ba5764'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('proc_BlanksHistoryTable','session')
    op.drop_column('proc_FitHistoryTable','session')
    op.add_column('proc_FitHistoryTable',
                  sa.Column('action_id', sa.INTEGER, sa.ForeignKey('proc_ActionTable.id')))

def downgrade():
    op.drop_constraint(
        'proc_fithistorytable_ibfk_2',
        'proc_FitHistoryTable',
        'foreignkey')
    op.drop_column('proc_FitHistoryTable','action_id')
    op.add_column('proc_BlanksHistoryTable', sa.Column('session', sa.String(40)))
    op.add_column('proc_FitHistoryTable', sa.Column('session', sa.String(40)))
