from sqlalchemy import *
from migrate import *

meta = MetaData()
t1 = Table('ProjectTable', meta,
            Column('id', Integer, primary_key=True),
            Column('name', String(40),
            ),
)
t2 = Table('UserTable', meta,
            Column('id', Integer, primary_key=True),
            Column('name', String(40)),
            Column('project_id', Integer)
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t1.create()
    t2.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    t1.drop()
    t2.drop()
