from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('IrradiationProductionTable', meta, autoload=True)
    col = Column('Cl3638', Float)
    cole = Column('Cl3638_err', Float)
    coln = Column('name', String(40))
    col.create(t)
    cole.create(t)
    coln.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('IrradiationProductionTable', meta, autoload=True)
    t.c.Cl3638.drop()
    t.c.Cl3638_err.drop()
    t.c.name.drop()

