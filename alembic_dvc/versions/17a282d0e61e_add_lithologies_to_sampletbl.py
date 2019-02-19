"""add lithologies to sampletbl

Revision ID: 17a282d0e61e
Revises: 7fb7364b821a
Create Date: 2019-02-19 16:17:08.690122

"""

# revision identifiers, used by Alembic.
revision = '17a282d0e61e'
down_revision = '7fb7364b821a'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('SampleTbl', sa.Column('lithology_class', sa.String(140)))
    op.add_column('SampleTbl', sa.Column('lithology_group', sa.String(140)))
    op.add_column('SampleTbl', sa.Column('lithology_type', sa.String(140)))


def downgrade():
    op.drop_column('SampleTbl', 'lithology_class')
    op.drop_column('SampleTbl', 'lithology_group')
    op.drop_column('SampleTbl', 'lithology_type')


