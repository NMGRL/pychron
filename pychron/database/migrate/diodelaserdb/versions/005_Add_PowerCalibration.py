from sqlalchemy import *
from migrate import *


meta = MetaData()

t1 = Table('PowerCalibrationTable', meta,
            Column('id', Integer, primary_key=True),
              Column('rundate', Date),
              Column('runtime', Time),

)
t2 = Table('PowerCalibrationPathTable', meta,
              Column('id', Integer, primary_key=True),
              Column('root', String(200)),
              Column('filename', String(80)),
              Column('power_calibration_id', Integer)
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
