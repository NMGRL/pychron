from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('gen_LabTable', meta, autoload=True)

    try:
        c = Column('note', String(140))
        c.create(t)
    except Exception:
        print 'column gen_LabTable.note already exists'

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('gen_LabTable', meta, autoload=True)
    t.c.note.drop()
