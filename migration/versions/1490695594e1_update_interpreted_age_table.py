"""update interpreted age table

Revision ID: 1490695594e1
Revises: 3d2790578104
Create Date: 2014-03-19 16:32:17.971706

"""

# revision identifiers, used by Alembic.
revision = '1490695594e1'
down_revision = '3d2790578104'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('proc_InterpretedAgeTable', 'wtd_kca',
                    new_column_name='kca',
                    existing_type=sa.Float)
    op.alter_column('proc_InterpretedAgeTable', 'wtd_kca_err', new_column_name='kca_err',
                    existing_type=sa.Float)

    op.add_column('proc_InterpretedAgeTable', sa.Column('kca_kind', sa.Float(32)))


def downgrade():
    # op.drop_column('proc_InterpretedAgeTable','arith_kca')
    # op.drop_column('proc_InterpretedAgeTable','arith_kca_err')
    op.drop_column('proc_InterpretedAgeTable', 'kca_kind')
    op.alter_column('proc_InterpretedAgeTable', 'kca',
                    new_column_name='wtd_kca',
                    existing_type=sa.Float)
    op.alter_column('proc_InterpretedAgeTable', 'kca_err', new_column_name='wtd_kca_err',
                    existing_type=sa.Float)