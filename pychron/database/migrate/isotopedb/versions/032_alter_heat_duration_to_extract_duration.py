from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine
    t = Table('meas_ExtractionTable', meta, autoload=True)
    t.c.heat_duration.alter(name='extract_duration')
    t.c.clean_up_duration.alter(name='cleanup_duration')
    t.c.heat_device_id.alter(name='extract_device_id')
def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData()
    meta.bind = migrate_engine
    t = Table('meas_ExtractionTable', meta, autoload=True)
    t.c.extract_duration.alter(name='heat_duration')
    t.c.cleanup_duration.alter(name='clean_up_duration')
    t.c.extract_device_id.alter(name='heat_device_id')
