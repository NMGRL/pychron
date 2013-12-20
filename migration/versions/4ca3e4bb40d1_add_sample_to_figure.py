"""add sample to figuretable

Revision ID: 4ca3e4bb40d1
Revises: 5517015226ba
Create Date: 2013-12-19 22:02:07.033017

"""

# revision identifiers, used by Alembic.
revision = '4ca3e4bb40d1'
down_revision = '5517015226ba'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_FigureSamplesTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('sample_id', sa.Integer),
                    sa.Column('figure_id', sa.Integer)
                    )


def downgrade():
    op.drop_table('proc_FigureSamplesTable')
