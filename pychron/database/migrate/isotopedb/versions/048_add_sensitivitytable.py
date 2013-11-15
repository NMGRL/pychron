from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint

meta = MetaData()
t = Table('gen_SensitivityTable', meta,
Column('id', Integer, primary_key=True),
Column('sensitivity', Float(32)),
Column('mass_spectrometer_id', Integer),
Column('user', String(40)),
Column('note', BLOB),
Column('create_date', DateTime)
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    t.create()
#
    tt = Table('meas_ExtractionTable', meta, autoload=True)
    c = Column('sensitivity_multiplier', Float)
    c.create(tt, populate_default=True)
#
    c = Column('sensitivity_id', Integer)
    c.create(tt)
#
    cons = ForeignKeyConstraint([tt.c.sensitivity_id], [t.c.id])
    cons.create()
#
    mst = Table('gen_MassSpectrometerTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t.c.mass_spectrometer_id], [mst.c.id])
    cons.create()



def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    mst = Table('gen_MassSpectrometerTable', meta, autoload=True)
    tt = Table('meas_ExtractionTable', meta, autoload=True)

    cons = ForeignKeyConstraint([t.c.mass_spectrometer_id], [mst.c.id])
    cons.drop()

    cons = ForeignKeyConstraint([tt.c.sensitivity_id], [t.c.id])
    cons.drop()

    tt.c.sensitivity_multiplier.drop()
    tt.c.sensitivity_id.drop()


    t.drop()


    # print mst.constraints
