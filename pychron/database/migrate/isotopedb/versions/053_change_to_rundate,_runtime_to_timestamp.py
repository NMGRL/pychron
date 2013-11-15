from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_AnalysisTable', meta, autoload=True)
    t.c.rundate.drop()
    t.c.runtime.drop()

    c = Column('analysis_timestamp', DateTime)
    try:
        c.create(t)
    except Exception, e:
        print 'column already exists'


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_AnalysisTable', meta, autoload=True)
    cd = Column('rundate', Date)
    ct = Column('runtime', Time)
    cd.create(t)
    ct.create(t)

    t.c.analysis_timestamp.drop()
