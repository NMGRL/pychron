from sqlalchemy import *
from migrate import *
meta = MetaData()
t = Table('ExtractionDeviceTable', meta,
Column('id', Integer, primary_key=True),
Column('name', String(80)),
Column('kind', String(80)),
Column('make', String(80)),
Column('model', String(80)),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t.drop()
