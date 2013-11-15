from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('flux_MonitorTable', meta, autoload=True)
    c = Column('name', String(80))
    c.create(t)
    c = Column('decay_constant_err', Float)
    c.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('flux_MonitorTable', meta, autoload=True)
    t.c.name.drop()
    t.c.decay_constant_err.drop()
