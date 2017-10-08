"""remove production from irradiation

Revision ID: 4fe417d5a155
Revises: 2839fc32e126
Create Date: 2016-01-14 13:19:48.087317

"""

# revision identifiers, used by Alembic.
revision = '4fe417d5a155'
down_revision = '2839fc32e126'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.drop_column('IrradiationTbl', 'production')


def downgrade():
    op.add_column('IrradiationTbl', sa.Column(sa.String(45), 'production'))
