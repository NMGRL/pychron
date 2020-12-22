"""add cryo_temp

Revision ID: 7d8af5fc1ca8
Revises: 4cefefc3ed78
Create Date: 2020-11-20 11:25:49.269295

"""

# revision identifiers, used by Alembic.
revision = '7d8af5fc1ca8'
down_revision = '4cefefc3ed78'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('AnalysisTbl', sa.Column('cryo_temperature', sa.Float))


def downgrade():
    op.drop_column('AnalysisTbl', 'cryo_temperature')
