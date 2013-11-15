from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_AnalysisPathTable', meta, autoload=True)
    t.drop()

    t = Table('meas_AnalysisTable', meta, autoload=True)
    c = Column('uuid', String(36))
    c.create(t)



def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_AnalysisPathTable', meta,
              Column('id', Integer, primary_key=True),
              Column('analysis_id', Integer),
              Column('root', String(200)),
              Column('filename', Integer(80)),
              )
    t.create()

    t = Table('meas_AnalysisTable', meta, autoload=True)
    t.c.uuid.drop()
