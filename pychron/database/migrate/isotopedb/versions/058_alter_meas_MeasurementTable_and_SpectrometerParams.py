from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    mt = Table('meas_MeasurementTable', meta, autoload=True)
    c = Column('spectrometer_parameters_id', Integer)
    c.create(mt)

    sp = Table('meas_SpectrometerParametersTable', meta, autoload=True)
    fk = ForeignKeyConstraint([mt.c.spectrometer_parameters_id], [sp.c.id])
    fk.create()

    fk = ForeignKeyConstraint([sp.c.measurement_id], [mt.c.id])
    fk.drop()
    sp.c.measurement_id.drop()

    c = Column('hash', String(32))
    c.create(sp)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.

    meta = MetaData(bind=migrate_engine)
    mt = Table('meas_MeasurementTable', meta, autoload=True)
    sp = Table('meas_SpectrometerParametersTable', meta, autoload=True)
    c = Column('measurement_id', Integer)
    c.create(sp)

    fk = ForeignKeyConstraint([sp.c.measurement_id], [mt.c.id])
    fk.create()
    fk = ForeignKeyConstraint([mt.c.spectrometer_parameters_id], [sp.c.id])
    fk.drop()

    mt.c.spectrometer_parameters_id.drop()
    sp.c.hash.drop()
