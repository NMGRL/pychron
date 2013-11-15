from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    for tn in ['AnalysisPath', 'Analysis', 'Experiment', 'Measurement', 'Extraction', 'Isotope']:
        tn = '{}Table'.format(tn)
        nt = 'meas_{}'.format(tn)
        t = Table(tn, meta, autoload=True)
        t.rename(nt)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    for tn in ['AnalysisPath', 'Analysis', 'Experiment', 'Measurement', 'Extraction', 'Isotope']:
        tn = 'meas_{}Table'.format(tn)
        nt = tn.replace('meas_', '')
        t = Table(tn, meta, autoload=True)
        t.rename(nt)
