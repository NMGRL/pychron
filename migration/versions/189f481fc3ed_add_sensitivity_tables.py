"""add sensitivity tables

Revision ID: 189f481fc3ed
Revises: 3609361b4b95
Create Date: 2014-01-14 19:47:45.158418

"""

# revision identifiers, used by Alembic.
revision = '189f481fc3ed'
down_revision = '3609361b4b95'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_SensitivityHistoryTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('create_date', sa.DateTime),
                    sa.Column('analysis_id',
                              sa.Integer,
                              sa.ForeignKey('meas_AnalysisTable.id')),
                    sa.Column('user', sa.String(40)))

    op.create_table('proc_SensitivityTable',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('value', sa.Float(32)),
                    sa.Column('error', sa.Float(32)),
                    sa.Column('history_id',sa.Integer,
                              sa.ForeignKey('proc_SensitivityHistoryTable.id')))

    op.add_column('proc_SelectedHistoriesTable',
                  sa.Column('selected_sensitivity_id',
                            sa.Integer,
                            sa.ForeignKey('proc_SensitivityHistoryTable.id')))

def downgrade():
    op.drop_constraint('proc_selectedhistoriestable_ibfk_1',
                       'proc_SelectedHistoriesTable',
                       'foreignkey')
    op.drop_column('proc_SelectedHistoriesTable', 'selected_sensitivity_id')

    op.drop_table('proc_SensitivityTable')
    op.drop_table('proc_SensitivityHistoryTable')
