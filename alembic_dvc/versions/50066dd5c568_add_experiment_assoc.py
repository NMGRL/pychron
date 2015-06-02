"""add experiment_association_tbl

Revision ID: 50066dd5c568
Revises: None
Create Date: 2015-06-02 14:36:39.644903

"""

# revision identifiers, used by Alembic.
revision = '50066dd5c568'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('ExperimentTbl',
                    sa.Column('name', sa.String(80), primary_key=True),
                    sa.Column('timestamp', sa.TIMESTAMP),
                    sa.Column('creator', sa.String(80), sa.ForeignKey('UserTbl.name')))

    op.create_table('ExperimentAssociationTbl',
                    sa.Column('idexperimentassociationTbl', sa.Integer, primary_key=True),
                    sa.Column('experiment_name', sa.String(80), sa.ForeignKey('ExperimentTbl.name')),
                    sa.Column('analysis_id', sa.Integer, sa.ForeignKey('AnalysisTbl.idanalysisTbl')))


def downgrade():
    op.drop_table('ExperimentAssociationTbl')
    op.drop_table('ExperimentTbl')
