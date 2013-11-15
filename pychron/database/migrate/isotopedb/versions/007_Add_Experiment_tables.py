from sqlalchemy import *
from migrate import *

meta = MetaData()

t1 = Table('ExperimentTable', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(40)),
)

t2 = Table('ExtractionTable', meta,
    Column('id', Integer, primary_key=True),
    Column('script_name', String(80)),
    Column('script_blob', BLOB),
    Column('heat_device_id', Integer),
    Column('position', Integer),
    Column('value', Float),
    Column('heat_duration', Float),
    Column('clean_up_duration', Float)
)
t3 = Table('MeasurementTable', meta,
    Column('id', Integer, primary_key=True),
    Column('script_name', String(80)),
    Column('script_blob', BLOB),
    Column('mass_spectrometer_id', Integer)
)

t4 = Table('MassSpectrometerTable', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(40))
)

t5 = Table('MolecularWeightTable', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(40)),
    Column('mass', Float)
)

t6 = Table('IsotopeTable', meta,
    Column('id', Integer, primary_key=True),
    Column('analysis_id', Integer),
    Column('detector_id', Integer),
    Column('molecular_weight_id', Integer)
)

tables = [t1, t2, t3, t4, t5, t6]

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
