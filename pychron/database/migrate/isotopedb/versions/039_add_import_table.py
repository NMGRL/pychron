from sqlalchemy import *
from migrate import *
meta = MetaData()
t = Table('gen_ImportTable', meta,
Column('id', Integer, primary_key=True),
Column('date', DateTime),
Column('user', String(80)),
Column('source_host', String(200)),
Column('source', String(200))
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()

    tt = Table('meas_AnalysisTable', meta, autoload=True)
    c = Column('import_id', Integer)
    c.create(tt)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t.drop()
    tt = Table('meas_AnalysisTable', meta, autoload=True)
    tt.c.import_id.drop()
