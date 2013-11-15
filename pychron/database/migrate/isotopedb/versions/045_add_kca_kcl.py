from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('irrad_ProductionTable', meta, autoload=True)
    c = Column('Ca_K', Float(32))
    ce = Column('Ca_K_err', Float(32))
    c.create(t)
    ce.create(t)

    c = Column('Cl_K', Float(32))
    ce = Column('Cl_K_err', Float(32))
    c.create(t)
    ce.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('irrad_ProductionTable', meta, autoload=True)
    t.c.Ca_K.drop()
    t.c.Cl_K.drop()

    t.c.Ca_K_err.drop()
    t.c.Cl_K_err.drop()
