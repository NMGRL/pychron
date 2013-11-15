from sqlalchemy import *
from migrate import *
meta = MetaData()
t = Table('proc_FitHistoryTable', meta,
Column('id', Integer, primary_key=True),
Column('analysis_id', Integer),
Column('create_date', DateTime),
Column('user', String(40)),
)
t1 = Table('proc_FitTable', meta,
Column('id', Integer, primary_key=True),
Column('history_id', Integer),
Column('isotope', String(40)),
Column('fit', String(40)),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()
    t1.create()

    st = Table('proc_SelectedHistoriesTable', meta, autoload=True)
    c = Column('selected_fits_id', Integer)
    c.create(st)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t.drop()
    t1.drop()

    st = Table('proc_SelectedHistoriesTable', meta, autoload=True)
    st.c.selected_fits_id.drop()
