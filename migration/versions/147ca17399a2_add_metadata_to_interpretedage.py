"""add metadata to interpretedage

Revision ID: 147ca17399a2
Revises: 1490695594e1
Create Date: 2014-03-21 17:18:06.594599

"""

# revision identifiers, used by Alembic.
revision = '147ca17399a2'
down_revision = '1490695594e1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_InterpretedAgeTable',
                  sa.Column('age_error_kind', sa.String(80)))
    op.add_column('proc_InterpretedAgeTable',
                  sa.Column('include_j_error_in_mean', sa.Boolean))
    op.add_column('proc_InterpretedAgeTable',
                  sa.Column('include_j_error_in_plateau', sa.Boolean))
    op.add_column('proc_InterpretedAgeTable',
                  sa.Column('include_j_error_in_individual_analyses',
                            sa.Boolean))


def downgrade():
    op.drop_column('proc_InterpretedAgeTable', 'age_error_kind')
    op.drop_column('proc_InterpretedAgeTable',
                   'include_j_error_in_mean')
    op.drop_column('proc_InterpretedAgeTable',
                   'include_j_error_in_plateau')
    op.drop_column('proc_InterpretedAgeTable',
                   'include_j_error_in_individual_analyses')


