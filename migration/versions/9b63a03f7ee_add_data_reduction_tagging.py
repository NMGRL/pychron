"""add data reduction tagging

Revision ID: 9b63a03f7ee
Revises: 30db613c85f8
Create Date: 2014-06-30 14:40:44.103815

"""

# revision identifiers, used by Alembic.
revision = '9b63a03f7ee'
down_revision = '30db613c85f8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('proc_DataReductionTagTable',
                    sa.Column('id', sa.INTEGER, primary_key=True),
                    sa.Column('name', sa.String(140)),
                    sa.Column('create_date', sa.DateTime),
                    sa.Column('comment', sa.BLOB),
                    sa.Column('user_id', sa.INTEGER, sa.ForeignKey('gen_UserTable.id')))

    op.create_table('proc_DataReductionTagSetTable',
                    sa.Column('id', sa.INTEGER, primary_key=True),
                    sa.Column('tag_id', sa.INTEGER, sa.ForeignKey('proc_DataReductionTagTable.id')),
                    sa.Column('analysis_id', sa.INTEGER, sa.ForeignKey('meas_AnalysisTable.id')),
                    sa.Column('selected_histories_id', sa.INTEGER, sa.ForeignKey('proc_SelectedHistoriesTable.id')))


def downgrade():
    op.drop_constraint('proc_datareductiontagtable_ibfk_1',
                       'proc_datareductiontagtable',
                       'foreignkey')

    op.drop_constraint('proc_datareductiontagsettable_ibfk_1',
                       'proc_datareductiontagsettable',
                       'foreignkey')

    op.drop_constraint('proc_datareductiontagsettable_ibfk_2',
                       'proc_datareductiontagsettable',
                       'foreignkey')

    op.drop_constraint('proc_datareductiontagsettable_ibfk_3',
                       'proc_datareductiontagsettable',
                       'foreignkey')

    op.drop_table('proc_DataReductionTagTable')
    op.drop_table('proc_DataReductionTagSetTable')
