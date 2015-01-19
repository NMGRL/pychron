"""add gain table

Revision ID: 40dae38fbfe8
Revises: 37edda381f28
Create Date: 2014-11-01 20:09:35.925118

"""

# revision identifiers, used by Alembic.
revision = '40dae38fbfe8'
down_revision = '37edda381f28'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('meas_GainHistoryTable',
                    sa.Column('id',sa.INTEGER, primary_key=True),
                    sa.Column('hash',sa.String(32)),
                    sa.Column('create_date', sa.DateTime),
                    sa.Column('user_id', sa.INTEGER, sa.ForeignKey('gen_UserTable.id')),
                    mysql_engine='InnoDB')

    op.create_table('meas_GainTable',
                    sa.Column('id',sa.INTEGER, primary_key=True),
                    sa.Column('value',sa.Float(32)),
                    sa.Column('history_id', sa.INTEGER,
                              sa.ForeignKey('meas_GainHistoryTable.id')),
                    sa.Column('detector_id',sa.INTEGER,
                              sa.ForeignKey('gen_DetectorTable.id')),
                    mysql_engine='InnoDB')

    op.add_column('meas_AnalysisTable',
                  sa.Column('gain_history_id',
                            sa.INTEGER,
                            sa.ForeignKey('meas_GainHistoryTable.id')))

def downgrade():
    try:
        op.drop_constraint('meas_analysistable_ibfk_9',
                       'meas_AnalysisTable','foreignkey')
    except:
        pass

    op.drop_column('meas_AnalysisTable', 'gain_history_id')
    op.drop_table('meas_GainTable')
    op.drop_table('meas_GainHistoryTable')

