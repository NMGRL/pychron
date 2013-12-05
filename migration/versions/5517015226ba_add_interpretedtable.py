"""add interpretedtables

Revision ID: 5517015226ba
Revises: 35a07261cd96
Create Date: 2013-12-04 17:47:20.013670

"""

# revision identifiers, used by Alembic.
revision = '5517015226ba'
down_revision = '35a07261cd96'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_InterpretedAgeHistoryTable',
                    sa.Column('id', sa.Integer, primary_key=True))
    op.create_table('proc_InterpretedAgeTable',
                    sa.Column('id', sa.Integer, primary_key=True))
    op.create_table('proc_InterpretedAgeSetTable',
                    sa.Column('id', sa.Integer, primary_key=True))

    #op.add_column('proc_InterpretedAgeHistoryTable', sa.Column('id', sa.Integer, primary_key=True))
    op.add_column('proc_InterpretedAgeHistoryTable', sa.Column('create_date', sa.TIMESTAMP,
                                                               server_default=sa.func.now()))

    op.add_column('proc_InterpretedAgeHistoryTable', sa.Column('user', sa.String(80)))
    op.add_column('proc_InterpretedAgeHistoryTable', sa.Column('lab_id', sa.Integer,
                                                               sa.ForeignKey('gen_LabTable.id')))

    #op.add_column('proc_InterpretedAgeTable', sa.Column('id', sa.Integer,primary_key=True))
    op.add_column('proc_InterpretedAgeTable', sa.Column('history_id', sa.Integer,
                                                        sa.ForeignKey('proc_InterpretedAgeHistoryTable.id')))
    op.add_column('proc_InterpretedAgeTable', sa.Column('age_kind', sa.String(32)))
    op.add_column('proc_InterpretedAgeTable', sa.Column('age', sa.Float))
    op.add_column('proc_InterpretedAgeTable', sa.Column('age_err', sa.Float))


    #op.add_column('proc_InterpretedAgeSetTable', sa.Column('id', sa.Integer,primary_key=True))
    op.add_column('proc_InterpretedAgeSetTable', sa.Column('analysis_id', sa.Integer,
                                                           sa.ForeignKey('meas_AnalysisTable.id')))
    op.add_column('proc_InterpretedAgeSetTable', sa.Column('interpreted_age_id', sa.Integer,
                                                           sa.ForeignKey('proc_InterpretedAgeTable.id')))
    op.add_column('proc_InterpretedAgeSetTable', sa.Column('forced_plateau_step', sa.Boolean))


def downgrade():
    op.drop_table('proc_InterpretedAgeSetTable')
    op.drop_table('proc_InterpretedAgeTable')
    op.drop_table('proc_InterpretedAgeHistoryTable')
