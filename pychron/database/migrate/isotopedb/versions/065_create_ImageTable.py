from sqlalchemy import *
from migrate import *
meta = MetaData()

# t = Table('med_ImageTable', meta,
t = Table('med_ImageTable', meta,
Column('id', Integer, primary_key=True),
Column('name', String(80)),
Column('create_date', DateTime),
Column('image', BLOB)
)
def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()

    tt = Table('meas_ExtractionTable', meta, autoload=True)
    c = Column('image_id', Integer)
    c.create(tt)

    fk = ForeignKeyConstraint([tt.c.image_id], [t.c.id])
    fk.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine


    tt = Table('meas_ExtractionTable', meta, autoload=True)
    fk = ForeignKeyConstraint([tt.c.image_id], [t.c.id])

    fk.drop()

    t.drop()
    tt.c.image_id.drop()
