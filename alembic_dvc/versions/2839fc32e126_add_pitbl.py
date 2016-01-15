"""add pitbl

Revision ID: 2839fc32e126
Revises: 35ca1ab00f2
Create Date: 2016-01-13 09:45:35.859143

"""

# revision identifiers, used by Alembic.
revision = '2839fc32e126'
down_revision = '35ca1ab00f2'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('PrincipalInvestigatorTbl', sa.Column('name', sa.String(140), primary_key=True),
                    sa.Column('email', sa.String(140)),
                    sa.Column('affiliation', sa.String(140)))

    op.add_column('ProjectTbl', sa.Column('principal_investigator', sa.String(140), sa.ForeignKey(
            'PrincipalInvestigatorTbl.name')))


def downgrade():
    op.drop_constraint('projecttbl_ibfk_1', 'ProjectTbl', type_='foreignkey')
    op.drop_column('ProjectTbl', 'principal_investigator')
    op.drop_table('PrincipalInvestigatorTbl')
