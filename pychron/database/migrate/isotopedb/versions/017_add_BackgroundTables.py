from sqlalchemy import *
from migrate import *

meta = MetaData()
bht = Table('proc_BackgroundsHistoryTable', meta,
Column('id', Integer, primary_key=True),
Column('analysis_id', Integer),
Column('create_date', DateTime),
Column('user', String(40)),
)
bt = Table('proc_BackgroundsTable', meta,
Column('id', Integer, primary_key=True),
Column('history_id', Integer),
Column('user_value', Float),
Column('user_error', Float),
Column('use_set', Boolean),
Column('isotope', String(40)),
Column('fit', String(40)),
)
bst = Table('proc_BackgroundsSetTable', meta,
Column('id', Integer, primary_key=True),
Column('background_analysis_id', Integer),
Column('backgrounds_id', Integer),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    bt.create()
    bst.create()
    bht.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    bt.drop()
    bst.drop()
    bht.drop()
