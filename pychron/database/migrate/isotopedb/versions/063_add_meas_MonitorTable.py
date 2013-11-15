from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_MonitorTable', meta,
              Column('id', Integer, primary_key=True),

              Column('analysis_id', Integer),
              Column('data', BLOB),
              Column('name', String(80)),
              Column('parameter', String(40)),
              Column('criterion', String(40)),
              Column('comparator', String(40)),
              Column('action', String(40)),
              Column('tripped', Boolean)
              )
    t.create()

    tt = Table('meas_AnalysisTable', meta, autoload=True)
    fk = ForeignKeyConstraint([t.c.analysis_id], [tt.c.id])
    fk.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_MonitorTable', meta, autoload=True)

    tt = Table('meas_AnalysisTable', meta, autoload=True)
    fk = ForeignKeyConstraint([t.c.analysis_id], [tt.c.id])
    fk.drop()

    t.drop()
