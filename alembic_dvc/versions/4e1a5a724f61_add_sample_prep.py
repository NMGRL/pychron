"""add_sample_prep

Revision ID: 4e1a5a724f61
Revises: df29b42d614
Create Date: 2016-05-11 13:16:30.339670

"""

# revision identifiers, used by Alembic.
revision = '4e1a5a724f61'
down_revision = 'df29b42d614'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('SamplePrepWorkerTbl',
                    sa.Column('name', sa.VARCHAR(32), primary_key=True),
                    sa.Column('fullname', sa.VARCHAR(45)),
                    sa.Column('email', sa.VARCHAR(45)),
                    sa.Column('phone', sa.VARCHAR(45)),
                    sa.Column('comment', sa.VARCHAR(140)))

    op.create_table('SamplePrepSessionTbl',
                    sa.Column('id', sa.INT, primary_key=True),
                    sa.Column('name', sa.VARCHAR(32)),
                    sa.Column('comment', sa.VARCHAR(140)),
                    sa.Column('worker_name', sa.String(32), sa.ForeignKey('SamplePrepWorkerTbl.name')),
                    sa.Column('start_date', sa.DATE),
                    sa.Column('end_date', sa.DATE))

    op.create_table('SamplePrepStepTbl',
                    sa.Column('id', sa.INT, primary_key=True),
                    sa.Column('sampleID', sa.INT, sa.ForeignKey('SampleTbl.id')),
                    sa.Column('sessionID', sa.INT, sa.ForeignKey('SamplePrepSessionTbl.id')),
                    sa.Column('crush', sa.VARCHAR(140)),
                    sa.Column('wash', sa.VARCHAR(140)),
                    sa.Column('sieve', sa.VARCHAR(140)),
                    sa.Column('frantz', sa.VARCHAR(140)),
                    sa.Column('acid', sa.VARCHAR(140)),
                    sa.Column('heavy_liquid', sa.VARCHAR(140)),
                    sa.Column('pick', sa.VARCHAR(140)),
                    sa.Column('status', sa.VARCHAR(32)),
                    sa.Column('comment', sa.VARCHAR(300)),
                    sa.Column('timestamp', sa.DATETIME),
                    sa.Column('added', sa.Boolean))

    op.create_table('SamplePrepImageTbl',
                    sa.Column('id', sa.INT, primary_key=True),
                    sa.Column('stepID', sa.INT, sa.ForeignKey('SamplePrepStepTbl.id')),
                    sa.Column('host', sa.VARCHAR(45)),
                    sa.Column('path', sa.VARCHAR(45)),
                    sa.Column('timestamp', sa.DATETIME))


def downgrade():
    op.drop_table('SamplePrepImageTbl')
    op.drop_table('SamplePrepStepTbl')
    op.drop_table('SamplePrepSessionTbl')
    op.drop_table('SamplePrepWorkerTbl')
