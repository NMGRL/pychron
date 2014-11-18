"""add preceding_id to blanks

Revision ID: 2a203d447c9c
Revises: 23aebdf4877c
Create Date: 2014-03-31 20:49:08.534616

"""

# revision identifiers, used by Alembic.
revision = '2a203d447c9c'
down_revision = '23aebdf4877c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_BlanksTable', sa.Column('preceding_id', sa.Integer,
                                                sa.ForeignKey('meas_AnalysisTable.id')))


def downgrade():
    op.drop_constraint('proc_blankstable_ibfk_2', 'proc_blankstable', 'foreignkey')
    op.drop_column('proc_BlanksTable', 'preceding_id')