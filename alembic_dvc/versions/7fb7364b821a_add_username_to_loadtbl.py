"""add username to LoadTbl

Revision ID: 7fb7364b821a
Revises: 090128c02529
Create Date: 2018-10-24 17:10:03.781293

"""

# revision identifiers, used by Alembic.
revision = '7fb7364b821a'
down_revision = '090128c02529'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('LoadTbl', sa.Column('username', sa.String(45)))
    op.create_foreign_key('LoadTbl_ibfk_2', 'LoadTbl', 'UserTbl', ['username'], ['name'])


def downgrade():
    op.drop_constraint('LoadTbl_ibfk_2', 'LoadTbl', type_='foreignkey')
    op.drop_column('LoadTbl', 'username')
