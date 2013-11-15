from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('gen_Usertable', meta, autoload=True)
    c = Column('password', String(128))
    c.create(t)
    c = Column('salt', String(32))
    c.create(t)

    c = Column('max_allowable_runs', Integer)
    c.create(t)
    c = Column('can_edit_scripts', Boolean)
    c.create(t)

    t.c.project_id.drop()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.

    meta = MetaData(bind=migrate_engine)
    t = Table('gen_Usertable', meta, autoload=True)

    t.c.password.drop()
    t.c.salt.drop()
    t.c.max_allowable_runs.drop()
    t.c.can_edit_scripts.drop()

    c = Column('project_id', Integer)
    c.create(t)
