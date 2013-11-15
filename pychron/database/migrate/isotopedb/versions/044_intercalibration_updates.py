from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_DetectorIntercalibrationTable', meta, autoload=True)
    c = Column('detector_id', Integer)
    c.create(t)

    t = Table('proc_DetectorIntercalibrationTable', meta, autoload=True)
    t.c.user_value.alter(type=Float(32))
    t.c.user_error.alter(type=Float(32))

    t = Table('proc_BlanksTable', meta, autoload=True)
    t.c.user_value.alter(type=Float(32))
    t.c.user_error.alter(type=Float(32))

    t = Table('proc_BackgroundsTable', meta, autoload=True)
    t.c.user_value.alter(type=Float(32))
    t.c.user_error.alter(type=Float(32))


    t = Table('proc_FitTable', meta, autoload=True)
    c = Column('filter_outliers', Boolean)
    c.create(t)
    c = Column('filter_outlier_iterations', Integer)
    c.create(t)
    c = Column('filter_outlier_std_devs', Integer)
    c.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_DetectorIntercalibrationTable', meta, autoload=True)
    t.c.detector_id.drop()

    t = Table('proc_FitTable', meta, autoload=True)
    t.c.filter_outliers.drop()
    t.c.filter_outlier_iterations.drop()
    t.c.filter_outlier_std_devs.drop()
