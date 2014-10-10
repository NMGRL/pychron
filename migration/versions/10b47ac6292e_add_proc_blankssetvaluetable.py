"""add proc_blankssetvaluetable

Revision ID: 10b47ac6292e
Revises: 239754394dbf
Create Date: 2014-09-16 22:31:34.028594

"""

# revision identifiers, used by Alembic.
revision = '10b47ac6292e'
down_revision = '239754394dbf'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_BlanksSetValueTable',
                 sa.Column('id', sa.Integer, primary_key=True),
                 sa.Column('value', sa.Float(32)),
                 sa.Column('error', sa.Float(32)),
                 sa.Column('analysis_id', sa.Integer, sa.ForeignKey('meas_AnalysisTable.id')),
                 sa.Column('blanks_id', sa.Integer, sa.ForeignKey('proc_BlanksTable.id')))


def downgrade():
    op.drop_table('proc_BlanksSetValueTable')
