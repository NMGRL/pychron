from sqlalchemy import *
from migrate import *
from migrate import ForeignKeyConstraint
meta = MetaData()
th = Table('proc_ArArHistoryTable', meta,
Column('id', Integer, primary_key=True),
Column('analysis_id', Integer),
Column('create_date', DateTime),
Column('user', String(40))
)
t = Table('proc_ArArTable', meta,
Column('id', Integer, primary_key=True),
Column('history_id', Integer),
Column('age', Float),
Column('age_err', Float)
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()
    th.create()

    tt = Table('proc_SelectedHistoriesTable', meta, autoload=True)
    c = Column('selected_arar_id', Integer)
    c.create(tt)

#    a = tt.c.selected_arar
    con = ForeignKeyConstraint([c], [t.c.id])
    con.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    tt = Table('proc_SelectedHistoriesTable', meta, autoload=True)

    con = ForeignKeyConstraint([tt.c.selected_arar_id], [t.c.id])
    con.drop()

    t.drop()
    th.drop()
    tt.c.selected_arar_id.drop()
