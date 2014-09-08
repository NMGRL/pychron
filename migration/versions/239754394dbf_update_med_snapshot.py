"""update med_snapshot

Revision ID: 239754394dbf
Revises: 4ab75910bd34
Create Date: 2014-09-07 09:17:41.685314

"""

# revision identifiers, used by Alembic.
revision = '239754394dbf'
down_revision = '4ab75910bd34'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('med_SnapshotTable', sa.Column('remote_path', sa.String(200)))


def downgrade():
    op.drop_column('med_SnapshotTable', 'remote_path')
