"""add archived to loadtbl

Revision ID: 35ca1ab00f2
Revises: 146580790cd
Create Date: 2016-01-08 12:32:49.891035

"""

# revision identifiers, used by Alembic.
revision = '35ca1ab00f2'
down_revision = '146580790cd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('LoadTbl', sa.Column('archived', sa.Boolean))


def downgrade():
    op.drop_column('LoadTbl', 'archived')
