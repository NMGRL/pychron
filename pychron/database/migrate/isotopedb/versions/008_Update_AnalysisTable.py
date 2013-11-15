from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('AnalysisTable', meta, autoload=True)

    col1 = Column('extraction_id', Integer)
    col2 = Column('measurement_id', Integer)
    col3 = Column('experiment_id', Integer)
    col4 = Column('endtime', Time)
    col5 = Column('irradiation_position_id', Integer)
    for c in [col1, col2, col3, col4, col5]:
        c.create(t)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('AnalysisTable', meta, autoload=True)
    t.c.extraction_id.drop()
    t.c.measurement_id.drop()
    t.c.experiment_id.drop()
    t.c.endtime.drop()
    t.c.irradiation_position_id.drop()
