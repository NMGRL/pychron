from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_ExtractionTable', meta, autoload=True)
    t.c.value.alter(name='extract_value')

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_ExtractionTable', meta, autoload=True)
    t.c.extract_value.alter(name='value')
