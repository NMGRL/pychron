from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint

meta = MetaData()
t = Table('proc_FigureTable', meta,
Column('id', Integer, primary_key=True),
Column('name', String(40)),
Column('project_id', Integer),
Column('create_date', DateTime),
Column('user', String(40)),
Column('note', BLOB),
)

t2 = Table('proc_FigureAnalysisTable', meta,
Column('id', Integer, primary_key=True),
Column('analysis_id', Integer),
Column('figure_id', Integer),
Column('status', Integer),
Column('graph', Integer),
Column('group', Integer)
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()
    t2.create()


    tt = Table('gen_ProjectTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t.c.project_id], [tt.c.id])
    cons.create()

    tt2 = Table('meas_AnalysisTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t2.c.analysis_id], [tt2.c.id])
    cons.create()

    cons = ForeignKeyConstraint([t2.c.figure_id], [tt2.c.id])
    cons.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    tt = Table('gen_ProjectTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t.c.project_id], [tt.c.id])
    cons.drop()

    tt2 = Table('meas_AnalysisTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t2.c.analysis_id], [tt2.c.id])
    cons.drop()

    cons = ForeignKeyConstraint([t2.c.figure_id], [tt2.c.id])
    cons.drop()

    t.drop()
    t2.drop()
