from sqlalchemy import *
from migrate import *
ts = [
    'LabTable', 'UserTable', 'SampleTable', 'ProjectTable',
    'AnalysisTypeTable', 'DetectorTable', 'ExtractionDeviceTable',
    'MaterialTable', 'MolecularWeightTable', 'MassSpectrometerTable'
    ]

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    for ti in ts:
        t = Table(ti, meta, autoload=True)
        t.rename('gen_{}'.format(ti))


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    for ti in ts:
        t = Table('gen_{}'.format(ti), meta, autoload=True)
        t.rename(ti)
