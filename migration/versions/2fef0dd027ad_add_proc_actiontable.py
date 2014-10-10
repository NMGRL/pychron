"""add proc_actiontable

Revision ID: 2fef0dd027ad
Revises: 44b716c5b268
Create Date: 2014-09-19 01:48:07.380058

"""

# revision identifiers, used by Alembic.
revision = '2fef0dd027ad'
down_revision = '44b716c5b268'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_ActionTable',
                    sa.Column('id', sa.INTEGER, primary_key=True),
                    sa.Column('create_date', sa.DateTime),
                    sa.Column('action', sa.BLOB),
                    sa.Column('session', sa.String(40)),
                    sa.Column('user_id', sa.INTEGER, sa.ForeignKey('gen_UserTable.id')))

    op.add_column('proc_BlanksHistoryTable',
                  sa.Column('action_id', sa.INTEGER, sa.ForeignKey('proc_ActionTable.id')))
def downgrade():
    op.drop_constraint(
        'proc_blankshistorytable_ibfk_2',
        'proc_BlanksHistoryTable',
        'foreignkey')

    op.drop_column('proc_BlanksHistoryTable','action_id')
    op.drop_table('proc_ActionTable')
