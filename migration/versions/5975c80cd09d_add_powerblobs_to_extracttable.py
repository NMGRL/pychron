"""add powerblobs to extracttable

Revision ID: 5975c80cd09d
Revises: 3816a8617056
Create Date: 2014-02-04 00:51:48.304355

"""

# revision identifiers, used by Alembic.
revision = '5975c80cd09d'
down_revision = '3816a8617056'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('meas_ExtractionTable', sa.Column('response_blob', sa.BLOB))
    op.add_column('meas_ExtractionTable', sa.Column('output_blob', sa.BLOB))


def downgrade():
    op.drop_column('meas_ExtractionTable', 'response_blob')
    op.drop_column('meas_ExtractionTable', 'output_blob')
