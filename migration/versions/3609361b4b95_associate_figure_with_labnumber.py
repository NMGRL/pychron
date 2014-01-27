"""associate figure with labnumber

Revision ID: 3609361b4b95
Revises: 22c2aac814b7
Create Date: 2014-01-05 12:21:23.261708

"""

# revision identifiers, used by Alembic.
from sqlalchemy.orm import sessionmaker

revision = '3609361b4b95'
down_revision = '22c2aac814b7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('proc_FigureSamplesTable',sa.Column('lab_id',
                                                      sa.Integer,
                                                      sa.ForeignKey('gen_LabTable.id')))

    sql = """
        update proc_FigureSamplesTable as f
        join gen_sampletable as s on f.sample_id=s.id
        join gen_labtable as l on s.id=l.sample_id
        set lab_id=l.id
    """

    # engine = create_engine('mysql://alexander:@localhost/alembic_content_migration_example')
    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    session.execute(sql)
    session.commit()
    session.close()

    op.rename_table('proc_FigureSamplesTable','proc_FigureLabTable')

def downgrade():
    op.drop_constraint('proc_figurelabtable_ibfk_1', 'proc_FigureLabTable', 'foreignkey')
    op.drop_column('proc_FigureLabTable', 'lab_id')
    op.rename_table('proc_FigureLabTable','proc_FigureSamplesTable')
