"""modify set_id

Revision ID: 5bfd1830564
Revises: 10b47ac6292e
Create Date: 2014-09-19 00:49:48.874340

"""

# revision identifiers, used by Alembic.
revision = '5bfd1830564'
down_revision = '10b47ac6292e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('proc_BlanksTable', 'set_id',
                    type_=sa.BIGINT,
                    existing_type=sa.INTEGER)

    op.alter_column('proc_BlanksSetTable', 'set_id',
                    type_=sa.BIGINT,
                    existing_type=sa.INTEGER)

def downgrade():
    op.alter_column('proc_BlanksTable', 'set_id',
                    type_=sa.INTEGER,
                    existing_type=sa.BIGINT)
    op.alter_column('proc_BlanksSetTable', 'set_id',
                    type_=sa.INTEGER,
                    existing_type=sa.BIGINT)