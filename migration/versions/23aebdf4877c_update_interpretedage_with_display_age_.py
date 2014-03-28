"""update interpretedage with display_age_units

Revision ID: 23aebdf4877c
Revises: 4604a2f4bef4
Create Date: 2014-03-28 08:19:26.316141

"""

# revision identifiers, used by Alembic.
revision = '23aebdf4877c'
down_revision = '4604a2f4bef4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_InterpretedAgeTable', sa.Column('display_age_units', sa.String(2)))


def downgrade():
    op.drop_column('proc_InterpretedAgeTable', 'display_age_units')
