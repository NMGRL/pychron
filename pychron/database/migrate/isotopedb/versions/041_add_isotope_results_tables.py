from sqlalchemy import *
from migrate import *

meta = MetaData()
t = Table('proc_IsotopeResultsTable', meta,
Column('id', Integer, primary_key=True),
Column('signal_', Float(Precision=32)),
Column('signal_err', Float(Precision=32)),
Column('isotope_id', Integer),
Column('history_id', Integer)  # use the fithistory table
)

t1 = Table('meas_SignalTable', meta,
Column('id', Integer, primary_key=True),
Column('data', BLOB),
Column('isotope_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()
    t1.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t.drop()
    t1.drop()
