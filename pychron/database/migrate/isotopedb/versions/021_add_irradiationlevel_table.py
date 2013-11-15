from sqlalchemy import *
from migrate import *
meta = MetaData()
ta = Table('IrradiationLevelTable', meta,
Column('id', Integer, primary_key=True),
Column('name', String(40)),
Column('holder_id', Integer),
Column('irradiation_id', Integer),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    ta.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    ta.drop()
