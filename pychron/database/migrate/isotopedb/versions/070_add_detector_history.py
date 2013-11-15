from sqlalchemy import *
from migrate import *

meta = MetaData()
det_hist_table = Table('proc_DetectorParamHistoryTable', meta,
                       Column('id', Integer, primary_key=True),
                       Column('user', String(40)),
                       Column('create_date', DateTime),
                       Column('analysis_id', Integer),
                       )
det_param_table = Table('proc_DetectorParamTable', meta,
                        Column('id', Integer, primary_key=True),
                        Column('detector_id', Integer),
                        Column('history_id', Integer),
                        Column('disc', Float),
                        Column('disc_error', Float),
                       )

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata

    det_hist_table.create()
    det_param_table.create()

    sh = Table('proc_SelectedHistoriesTable', meta, autoload=True)
    c = Column('selected_det_param_id', Integer)
    c.create(sh)

    fk = ForeignKeyConstraint([sh.c.selected_det_param_id], [det_hist_table.c.id])
    fk.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    # Operations to reverse the above upgrade go here.

    sh = Table('proc_SelectedHistoriesTable', meta, autoload=True)

    fk = ForeignKeyConstraint([sh.c.selected_det_param_id], [det_hist_table.c.id])
    fk.drop()

    det_hist_table.drop()
    det_param_table.drop()

    sh.c.selected_det_param_id.drop()
