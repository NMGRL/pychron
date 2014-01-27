"""add kind to figprefs

Revision ID: 38fc7371a444
Revises: 4ca3e4bb40d1
Create Date: 2013-12-20 11:15:56.370509

"""

# revision identifiers, used by Alembic.
revision = '38fc7371a444'
down_revision = '4ca3e4bb40d1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_FigurePrefTable',sa.Column('kind', sa.String(40)))
    op.alter_column('proc_FigurePrefTable', 'options_pickle',
                    existing_type=sa.BLOB,
                    new_column_name='options')

def downgrade():
    op.drop_column('proc_FigurePrefTable','kind')
    op.alter_column('proc_FigurePrefTable', 'options',
                    existing_type=sa.BLOB,
                    new_column_name='options_pickle')