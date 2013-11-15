from sqlalchemy import *
from migrate import *
meta = MetaData()
flux = Table('FluxTable', meta,
Column('id', Integer, primary_key=True),
Column('j', Float),
Column('j_err', Float),
Column('irradiation_position_id', Integer),
Column('flux_set_id', Integer)
)

fset = Table('FluxSetTable', meta,
Column('id', Integer, primary_key=True),
Column('name', String(40)),
Column('note', BLOB),
Column('flux_monitor_id', Integer)
)

fmon = Table('FluxMonitorTable', meta,
Column('id', Integer, primary_key=True),
Column('decay_constant', Float),
Column('age', Float),
Column('age_err', Float),
Column('sample_id', Integer),
)
tables = [flux, fset, fmon]
def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    for t in tables:
        t.create()

    t = Table('IrradiationPositionTable', MetaData(bind=migrate_engine), autoload=True)
    col = Column('flux_id', Integer)
    col.create(t)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    for t in tables:
        t.drop()

    t = Table('IrradiationPositionTable', MetaData(bind=migrate_engine), autoload=True)
    t.c.flux_id.drop()
