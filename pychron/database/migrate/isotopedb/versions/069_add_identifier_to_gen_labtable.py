from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('gen_LabTable', meta, autoload=True)
    c = Column('identifier', String(45))
    try:
        c.create(t)
    except Exception, e:
        print 'Column already exists. {}'.format('identifier')
        print e

    t.c.labnumber.drop()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('gen_LabTable', meta, autoload=True)
    t.c.identifier.drop()
    c = Column('labnumber', Integer)
    c.create(t)
