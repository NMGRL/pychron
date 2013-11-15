from sqlalchemy import *
from migrate import *
meta = MetaData()

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t = Table('meas_ExtractionTable', meta, autoload=True)
    c = Column('experiment_blob', BLOB)
    c.create(t)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t = Table('meas_ExtractionTable', meta, autoload=True)
    t.c.experiment_blob.drop()
