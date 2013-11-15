from sqlalchemy import *
from migrate import *
meta = MetaData()
t = Table('meas_PositionTable', meta,
Column('id', Integer, primary_key=True),
Column('position', Integer),
Column('x', Float),
Column('y', Float),
Column('z', Float),
Column('extraction_id', Integer)
)
def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata

    meta.bind = migrate_engine
    t.create()

    tt = Table('meas_ExtractionTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t.c.extraction_id], [tt.c.id])
    cons.create()

    tt.c.position.drop()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.

    meta.bind = migrate_engine
    tt = Table('meas_ExtractionTable', meta, autoload=True)
    c = Column('position', Integer)
    c.create(tt)

    cons = ForeignKeyConstraint([t.c.extraction_id], [tt.c.id])
    cons.drop()

    t.drop()
