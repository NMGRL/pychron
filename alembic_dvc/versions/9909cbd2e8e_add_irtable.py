"""add irtable

Revision ID: 9909cbd2e8e
Revises: 1ca68590acc1
Create Date: 2016-06-27 15:52:53.069969

"""

# revision identifiers, used by Alembic.
revision = '9909cbd2e8e'
down_revision = '1ca68590acc1'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('IRTbl',
                    sa.Column('ir', sa.VARCHAR(32), primary_key=True),
                    sa.Column('principal_investigator_id', sa.INTEGER, sa.ForeignKey(
                        'PrincipalInvestigatorTbl.id')),
                    sa.Column('institution', sa.VARCHAR(140)),
                    sa.Column('checkin_date', sa.TIMESTAMP),
                    sa.Column('lab_contact', sa.VARCHAR(140), sa.ForeignKey('UserTbl.name')),
                    sa.Column('comment', sa.BLOB)
                    )


def downgrade():
    op.drop_table('IRTbl')
