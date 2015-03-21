"""add source to flux_history

Revision ID: 502bd4123969
Revises: 15713811ac8f
Create Date: 2014-12-12 15:47:04.231696

"""

# revision identifiers, used by Alembic.
revision = '502bd4123969'
down_revision = '15713811ac8f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('flux_HistoryTable', sa.Column('source', sa.String(140)))


def downgrade():
    op.drop_column('flux_HistoryTable','source')
