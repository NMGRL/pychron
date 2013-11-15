from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    sh = Table('proc_SelectedHistoriesTable', meta, autoload=True)
    try:
        a = Table('proc_ArArTable', meta, autoload=True)
        fk = ForeignKeyConstraint([sh.c.selected_arar_id], [a.c.id])
        fk.drop()
    except:
        pass

    a = Table('proc_ArArHistoryTable', meta, autoload=True)
    fk = ForeignKeyConstraint([sh.c.selected_arar_id], [a.c.id])
    fk.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    sh = Table('proc_SelectedHistoriesTable', meta, autoload=True)

    a = Table('proc_ArArHistoryTable', meta, autoload=True)
    fk = ForeignKeyConstraint([sh.c.selected_arar_id], [a.c.id])
    fk.drop()
