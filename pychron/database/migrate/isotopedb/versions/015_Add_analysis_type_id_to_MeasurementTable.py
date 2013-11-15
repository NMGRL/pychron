from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata

    meta = MetaData(bind=migrate_engine)
    tab = Table('MeasurementTable', meta, autoload=True)
    col = Column('analysis_type_id', Integer)

    meta.bind = migrate_engine
    col.create(tab)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    tab = Table('MeasurementTable', meta, autoload=True)
    tab.c.analysis_type_id.drop()
