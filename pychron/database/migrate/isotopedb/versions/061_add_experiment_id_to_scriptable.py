from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_ExtractionTable', meta, autoload=True)
    c = Column('experiment_blob_id', Integer)
    tt = Table('meas_ScriptTable', meta, autoload=True)
    try:
        c.create(t)
    except:
        pass
    t.c.experiment_blob.drop()

    fk = ForeignKeyConstraint([t.c.experiment_blob_id], [tt.c.id])
    fk.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('meas_ExtractionTable', meta, autoload=True)
    tt = Table('meas_ScriptTable', meta, autoload=True)

    fk = ForeignKeyConstraint([t.c.experiment_blob_id], [tt.c.id])
    fk.drop()

    c = Column('experiment_blob', BLOB)
    c.create(t)
    t.c.experiment_blob_id.drop()

