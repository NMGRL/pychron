from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    mt = Table('meas_MeasurementTable', meta, autoload=True)
    et = Table('meas_ExtractionTable', meta, autoload=True)

    mt.c.script_blob.drop()
    mt.c.hash.drop()
    mt.c.script_name.drop()

    et.c.script_blob.drop()
    et.c.hash.drop()
    et.c.script_name.drop()

    c = Column('script_id', Integer)
    c.create(mt)
    c = Column('script_id', Integer)
    c.create(et)

    st = Table('meas_ScriptTable', meta,
             Column('id', Integer, primary_key=True),
             Column('name', String(80)),
             Column('hash', String(32)),
             Column('blob', BLOB)
             )
    st.create()

    fk = ForeignKeyConstraint([mt.c.script_id], [st.c.id])
    fk.create()
    fk = ForeignKeyConstraint([et.c.script_id], [st.c.id])
    fk.create()



def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    mt = Table('meas_MeasurementTable', meta, autoload=True)
    et = Table('meas_ExtractionTable', meta, autoload=True)
    st = Table('meas_ScriptTable', meta, autoload=True)

    fk = ForeignKeyConstraint([mt.c.script_id], [st.c.id])
    fk.drop()
    fk = ForeignKeyConstraint([et.c.script_id], [st.c.id])
    fk.drop()

    st.drop()

    c = Column('script_blob', BLOB)
    c.create(mt)
    c = Column('hash', String(32))
    c.create(mt)
    c = Column('script_name', String(80))
    c.create(mt)
# #
    c = Column('script_blob', BLOB)
    c.create(et)
    c = Column('hash', String(32))
    c.create(et)
    c = Column('script_name', BLOB)
    c.create(et)

    mt.c.script_id.drop()
    et.c.script_id.drop()
