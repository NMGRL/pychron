from sqlalchemy import *
from migrate import *
meta = MetaData()

t1 = Table('meas_SpectrometerParametersTable', meta,
Column('id', Integer, primary_key=True),
Column('extraction_lens', Float),
Column('ysymmetry', Float),
Column('zsymmetry', Float),
Column('zfocus', Float),
Column('measurement_id', Integer)
)
t2 = Table('meas_SpectrometerDeflectionsTable', meta,
Column('id', Integer, primary_key=True),
Column('detector_id', Integer),
Column('measurement_id', Integer),
Column('deflection', Float)
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t1.create()
    t2.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t1.drop()
    t2.drop()
