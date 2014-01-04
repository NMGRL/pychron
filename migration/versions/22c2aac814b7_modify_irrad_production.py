"""modify irrad_production

Revision ID: 22c2aac814b7
Revises: 46776b675c41
Create Date: 2014-01-03 17:08:25.220591

"""

# revision identifiers, used by Alembic.
revision = '22c2aac814b7'
down_revision = '46776b675c41'

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from alembic import op


def upgrade():
    op.add_column('irrad_LevelTable', sa.Column('production_id',
                                                sa.Integer,
                                                sa.ForeignKey('irrad_ProductionTable.id')))
    sql="""
        update
        irrad_leveltable as lt
        join irrad_IrradiationTable as ir on lt.irradiation_id = ir.id
        set lt.production_id = ir.irradiation_production_id
    """

    # engine = create_engine('mysql://alexander:@localhost/alembic_content_migration_example')
    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    session.execute(sql)
    session.commit()
    session.close()
    # print op.

def downgrade():
    op.drop_constraint('irrad_leveltable_ibfk_1', 'irrad_LevelTable','foreignkey')
    op.drop_column('irrad_LevelTable', 'production_id')
