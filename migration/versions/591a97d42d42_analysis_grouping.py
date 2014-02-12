"""analysis grouping

Revision ID: 591a97d42d42
Revises: 33af744196bc
Create Date: 2014-02-11 13:40:07.664778

"""

# revision identifiers, used by Alembic.
revision = '591a97d42d42'
down_revision = '33af744196bc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_AnalysisGroupTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String(80)),
                    sa.Column('last_modified', sa.TIMESTAMP,
                              server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
                    sa.Column('create_date', sa.TIMESTAMP,
                              default=sa.func.now()))

    op.create_table('proc_AnalysisGroupSetTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('group_id', sa.Integer),
                    sa.Column('analysis_id', sa.Integer))


def downgrade():
    op.drop_table('proc_AnalysisGroupTable')
    op.drop_table('proc_AnalysisSetTable')
