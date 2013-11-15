from sqlalchemy import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_TagTable', meta, autoload=True)

    for a in ('ideo', 'spec', 'iso'):
        c = Column('omit_{}'.format(a), Boolean)
        c.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_TagTable', meta, autoload=True)
    for a in ('ideo', 'spec', 'iso'):
        col = getattr(t.c, 'omit_{}'.format(a))
        col.drop(t)