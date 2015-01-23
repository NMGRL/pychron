"""add note level

Revision ID: 52f976e8c538
Revises: 2a77d61f4156
Create Date: 2015-01-20 16:47:34.858884

"""

# revision identifiers, used by Alembic.
revision = '52f976e8c538'
down_revision = '2a77d61f4156'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('irrad_LevelTable', sa.Column('note', sa.BLOB))


def downgrade():
    op.drop_column('irrad_LevelTable', 'note')
