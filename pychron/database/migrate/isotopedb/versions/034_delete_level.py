from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('irrad_IrradiationTable', meta, autoload=True)
    t.c.level.drop()

    t = Table('irrad_PositionTable', meta, autoload=True)
    t.c.irradiation_holder_id.drop()

    t = Table('flux_HistoryTable', meta, autoload=True)
    t.c.name.drop()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('irrad_IrradiationTable', meta, autoload=True)
    c = Column('level', String(80))
    c.create(t)

    t = Table('irrad_PositionTable', meta, autoload=True)
    c = Column('irradiation_holder_id', Integer)
    c.create(t)

    t = Table('flux_HistoryTable', meta, autoload=True)
    c = Column('name', Integer)
    c.create(t)
