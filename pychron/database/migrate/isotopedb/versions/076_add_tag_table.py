from sqlalchemy import *
from migrate import *

meta = MetaData()
t = Table('proc_TagTable', meta,
          Column('name', String(40), primary_key=True),
          Column('user', String(40)),
          Column('create_date', DateTime),
          )

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata

    meta.bind = migrate_engine
    t.create()

    at = Table('meas_AnalysisTable', meta, autoload=True)
    c = Column('tag', String(40))
    c.create(at)

#     fk = ForeignKeyConstraint([at.c.tag], [t.c.name])
#     fk.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    at = Table('meas_AnalysisTable', meta, autoload=True)
#     fk = ForeignKeyConstraint([at.c.tag], [t.c.name])
#     fk.drop()

    t.drop()

    at.c.tag.drop()
