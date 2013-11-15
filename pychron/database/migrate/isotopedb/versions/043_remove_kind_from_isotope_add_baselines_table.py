from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_IsotopeTable', meta, autoload=True)
#    t.c.kind.drop()

#    t=Table('meas_Baseline')
def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.

    meta = MetaData(bind=migrate_engine)
    t = Table('meas_IsotopeTable', meta, autoload=True)
    c = Column('kind', String(50))
    c.create(t)
