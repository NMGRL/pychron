from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('AnalysisTable', meta, autoload=True)
    col = Column('lab_id', Integer)
    col.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('AnalysisTable', meta, autoload=True)
    t.c.lab_id.drop()

