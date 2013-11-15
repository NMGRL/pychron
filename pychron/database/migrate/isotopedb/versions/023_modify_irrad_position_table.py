from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('irrad_PositionTable', meta, autoload=True)
    t.c.irradiation_id.alter(name='level_id')


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('irrad_PositionTable', meta, autoload=True)
    t.c.level_id.alter(name='irradiation_id')
