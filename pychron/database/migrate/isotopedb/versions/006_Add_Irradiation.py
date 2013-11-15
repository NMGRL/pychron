from sqlalchemy import *
from migrate import *

meta = MetaData()
t0 = Table('IrradiationPositionTable', meta,
    Column('id', Integer, primary_key=True),
    Column('irradiation_id', Integer),
    Column('irradiation_holder_id', Integer)
)
t1 = Table("IrradiationTable", meta,
    Column('id', Integer, primary_key=True),
    Column('irradiation_production_id', Integer),
    Column('irradiation_chronology_id', Integer),
    Column('name', String(40)),
    Column('level', String(40))
)
t2 = Table("IrradiationProductionTable", meta,
    Column('id', Integer, primary_key=True),
    Column('Ca3637', Float),
    Column('Ca3637_err', Float),
    Column('Ca3837', Float),
    Column('Ca3837_err', Float),
    Column('Ca3937', Float),
    Column('Ca3937_err', Float),

    Column('K3739', Float),
    Column('K3739_err', Float),
    Column('K3839', Float),
    Column('K3839_err', Float),
    Column('K4039', Float),
    Column('K4039_err', Float),
)
t3 = Table("IrradiationChronologyTable", meta,
    Column('id', Integer, primary_key=True),
    Column('chronology', BLOB)
)
t4 = Table("IrradiationHolderTable", meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(40)),
    Column('geometry', BLOB)
)

tables = [t0, t1, t2, t3, t4]

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    for t in tables:
        t.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    for t in tables:
        t.drop()
