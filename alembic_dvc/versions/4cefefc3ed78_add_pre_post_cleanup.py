"""add pre,post cleanup

Revision ID: 4cefefc3ed78
Revises: 7497821c0290
Create Date: 2020-01-13 15:30:14.549189

"""

# revision identifiers, used by Alembic.
revision = '4cefefc3ed78'
down_revision = '7497821c0290'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('AnalysisTbl', sa.Column('pre_cleanup', sa.Float))
    op.add_column('AnalysisTbl', sa.Column('post_cleanup', sa.Float))


def downgrade():
    op.drop_column('AnalysisTbl', 'pre_cleanup')
    op.drop_column('AnalysisTbl', 'post_cleanup')
