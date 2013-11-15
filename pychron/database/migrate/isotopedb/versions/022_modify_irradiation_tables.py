from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    for tn in ['Chronology', 'Holder', 'Level', 'Position', 'Production']:
        tn = 'Irradiation{}Table'.format(tn)
        nt = tn.replace('Irradiation', 'irrad_')
        t = Table(tn, meta, autoload=True)
        t.rename(nt)
    t = Table('IrradiationTable', meta, autoload=True)
    t.rename('irrad_IrradiationTable')

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    for tn in ['Chronology', 'Holder', 'Level', 'Position', 'Production']:
        tn = 'irrad_{}Table'.format(tn)
        nt = tn.replace('irrad_', 'Irradiation')
        t = Table(tn, meta, autoload=True)
        t.rename(nt)
    t = Table('irrad_IrradiationTable', meta, autoload=True)
    t.rename('IrradiationTable')
