from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('LabTable', meta, autoload=True)
    t.c.aliquot.drop()

    t = Table('meas_AnalysisTable', meta, autoload=True)
    col = Column('aliquot', Integer)
    col.create(t)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('LabTable', meta, autoload=True)
    col = Column('aliquot', Integer)
    col.create(t)

    t = Table('meas_AnalysisTable', meta, autoload=True)
    t.c.aliquot.drop()

