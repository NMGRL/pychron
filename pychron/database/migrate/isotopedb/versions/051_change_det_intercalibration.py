from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):


    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_DetectorIntercalibrationSetTable', meta, autoload=True)
    t.c.detector_intercalibration_analysis_id.alter(name='ic_analysis_id')
#    t.c.intercalibration_analysis_id.alter(name='intercal_analysis_id')
    t.c.detector_intercalibration_id.alter(name='intercalibration_id')
#
    t = Table('proc_SelectedHistoriesTable', meta, autoload=True)
    t.c.selected_detector_intercalibration_id.alter(name='selected_det_intercal_id')

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_DetectorIntercalibrationSetTable', meta, autoload=True)
#    t.c.intercalibration_analysis_id.alter(name='detector_intercalibration_analysis_id')
    t.c.ic_analysis_id.alter(name='detector_intercalibration_analysis_id')
    t.c.intercalibration_id.alter(name='detector_intercalibration_id')

    t = Table('proc_SelectedHistoriesTable', meta, autoload=True)
    t.c.selected_det_intercal_id.alter(name='selected_detector_intercalibration_id')






