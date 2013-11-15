from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)

    t = Table('FluxTable', meta, autoload=True)
    t.rename('flux_FluxTable')
    t.c.flux_set_id.alter(name='history_id')
    t.c.irradiation_position_id.drop()

    t = Table('FluxSetTable', meta, autoload=True)
    t.rename('flux_HistoryTable')
#    t.c.name.drop()
    c = Column('irradiation_position_id', Integer)
    c.create(t)

    t = Table('FluxMonitorTable', meta, autoload=True)
    t.rename('flux_MonitorTable')
#    c = Column('name', String(80))
#    c.create(t)
#    c = Column('decay_constant_err', Float)
#    c.create(t)

    t = Table('LabTable', meta, autoload=True)
    c = Column('selected_flux_id', Integer)
    c.create(t)
#
    t = Table('irrad_PositionTable', meta, autoload=True)
    c = Column('flux_id', Integer)
    c.drop(t)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('flux_FluxTable', meta, autoload=True)
    t.rename('FluxTable')
    t.c.history_id.alter(name='flux_set_id')
    c = Column('irradiation_position_id', Integer)
    c.create(t)

    t = Table('flux_HistoryTable', meta, autoload=True)
    t.rename('FluxSetTable')
#    c = Column('name', String(80))
#    c.create(t)
    t.c.irradiation_position_id.drop()

    t = Table('flux_MonitorTable', meta, autoload=True)
    t.rename('FluxMonitorTable')
#    t.c.name.drop()
#    t.c.decay_constant_err.drop()

    t = Table('LabTable', meta, autoload=True)
    t.c.selected_flux_id.drop()

    t = Table('irrad_PositionTable', meta, autoload=True)
    c = Column('flux_id', Integer)
    c.create(t)

