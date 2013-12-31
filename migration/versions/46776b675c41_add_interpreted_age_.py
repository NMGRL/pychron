"""add interpreted age group

Revision ID: 46776b675c41
Revises: b5443ca152f
Create Date: 2013-12-31 15:26:40.208030

"""

# revision identifiers, used by Alembic.
revision = '46776b675c41'
down_revision = 'b5443ca152f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_InterpretedAgeGroupHistoryTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String(80)),
                    sa.Column('project_id', sa.Integer),
                    sa.Column('create_date', sa.DateTime))

    op.create_table('proc_InterpretedAgeGroupSetTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('group_id', sa.Integer),
                    sa.Column('interpreted_age_id', sa.Integer))


def downgrade():
    op.drop_table('proc_InterpretedAgeGroupHistoryTable')
    op.drop_table('proc_InterpretedAgeGroupSetTable')
