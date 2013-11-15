from sqlalchemy import *
from migrate import *

meta = MetaData()
bht = Table('proc_SelectedHistoriesTable', meta,
Column('id', Integer, primary_key=True),
Column('analysis_id', Integer),
Column('selected_blanks_id', Integer),
Column('selected_backgrounds_id', Integer),
Column('selected_detector_intercalibration_id', Integer),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    bht.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    bht.drop()
