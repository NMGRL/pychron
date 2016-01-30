"""add grainsize to material

Revision ID: df29b42d614
Revises: fb8088a2da0
Create Date: 2016-01-24 18:01:12.542826

"""

# revision identifiers, used by Alembic.
revision = 'df29b42d614'
down_revision = 'fb8088a2da0'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('MaterialTbl', sa.Column('grainsize', sa.String(80)))


def downgrade():
    op.drop_column('MaterialTbl', 'grainsize')
