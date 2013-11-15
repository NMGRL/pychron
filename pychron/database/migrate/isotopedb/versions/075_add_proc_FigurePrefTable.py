from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint

meta = MetaData()
t = Table('proc_FigurePrefTable', meta,
          Column('id', Integer, primary_key=True),
          Column('figure_id', Integer),
          Column('xbounds', String(80)),
          Column('ybounds', String(80)),
          Column('options_pickle', BLOB)
          )

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine

    t.create()

    tt = Table('proc_FigureTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t.c.figure_id], [tt.c.id])
    cons.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    tt = Table('proc_FigureTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t.c.figure_id], [tt.c.id])
    cons.drop()

    t.drop()
