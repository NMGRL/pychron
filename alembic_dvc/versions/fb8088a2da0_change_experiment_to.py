"""change experiment to repository

Revision ID: fb8088a2da0
Revises: 4fe417d5a155
Create Date: 2016-01-14 13:34:47.542361

"""

# revision identifiers, used by Alembic.
revision = 'fb8088a2da0'
down_revision = '4fe417d5a155'

import sqlalchemy as sa
from alembic import op


def upgrade():
    # op.drop_table('ExperimentAssociationTbl')
    # op.drop_table('ExperimentTbl')

    op.create_table('RepositoryTbl',
                    sa.Column('name', sa.String(80), primary_key=True),
                    sa.Column('principal_investigator', sa.String(140), sa.ForeignKey(
                            'PrincipalInvestigatorTbl.name')),
                    mysql_engine='InnoDB', )

    op.create_table('RepositoryAssociationTbl',
                    sa.Column('idrepositoryassociationTbl', sa.Integer, primary_key=True),
                    sa.Column('repository', sa.String(80), sa.ForeignKey('RepositoryTbl.name')),
                    sa.Column('analysisID', sa.Integer, sa.ForeignKey('AnalysisTbl.idanalysisTbl')),
                    mysql_engine='InnoDB', )


def downgrade():
    pass
