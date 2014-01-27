"""add columns to interpreted_ages

Revision ID: 4a5e23eb4fae
Revises: 30c5c9f2d9dc
Create Date: 2013-12-22 08:47:06.056810

"""

# revision identifiers, used by Alembic.
revision = '4a5e23eb4fae'
down_revision = '30c5c9f2d9dc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_InterpretedAgeTable', sa.Column('mswd', sa.Float))
    op.add_column('proc_InterpretedAgeTable', sa.Column('wtd_kca', sa.Float))
    op.add_column('proc_InterpretedAgeTable', sa.Column('wtd_kca_err', sa.Float))


def downgrade():
    op.drop_column('proc_InterpretedAgeTable', 'mswd')
    op.drop_column('proc_InterpretedAgeTable', 'wtd_kca')
    op.drop_column('proc_InterpretedAgeTable', 'wtd_kca_err')
