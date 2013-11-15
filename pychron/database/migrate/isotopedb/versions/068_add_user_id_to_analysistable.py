from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    tt = Table('meas_AnalysisTable', meta, autoload=True)
    c = Column('user_id', Integer)
    c.create(tt)
    t = Table('gen_UserTable', meta, autoload=True)
    fk = ForeignKeyConstraint([tt.c.user_id], [t.c.id])
    fk.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    tt = Table('meas_AnalysisTable', meta, autoload=True)
    t = Table('gen_UserTable', meta, autoload=True)

    fk = ForeignKeyConstraint([tt.c.user_id], [t.c.id])
    fk.drop()

    tt.c.user_id.drop()
