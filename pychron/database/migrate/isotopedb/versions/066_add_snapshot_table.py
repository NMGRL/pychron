from sqlalchemy import *
from migrate import *

meta = MetaData()
t = Table('med_SnapshotTable', meta,
Column('id', Integer, primary_key=True),
Column('create_date', DateTime),
Column('extraction_id', Integer),
Column('path', String(200)),
Column('image', BLOB),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()

    tt = Table('meas_ExtractionTable', meta, autoload=True)
    fk = ForeignKeyConstraint([t.c.extraction_id], [tt.c.id])
    fk.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    tt = Table('meas_ExtractionTable', meta, autoload=True)
    fk = ForeignKeyConstraint([t.c.extraction_id], [tt.c.id])
    fk.drop()

    t.drop()
