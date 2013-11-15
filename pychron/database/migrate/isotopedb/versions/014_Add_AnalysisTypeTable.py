from sqlalchemy import *
from migrate import *
meta = MetaData()
t0 = Table('AnalysisTypeTable', meta,
Column('id', Integer, primary_key=True),
Column('name', String(40), primary_key=True)
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t0.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t0.drop()
