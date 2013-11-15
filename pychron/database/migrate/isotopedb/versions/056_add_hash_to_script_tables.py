from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)

    for n in ['Measurement', 'Extraction']:
        t = Table('meas_{}Table'.format(n), meta, autoload=True)
        c = Column('hash', String(40))
        c.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)

    for n in ['Measurement', 'Extraction']:
        t = Table('meas_{}Table'.format(n), meta, autoload=True)
        t.c.hash.drop()
