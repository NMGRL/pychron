from sqlalchemy import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta=MetaData(bind=migrate_engine)
    t=Table('meas_ExtractionTable', meta, autoload=True)

    c=Column('beam_diameter', Float)
    c.create(t)

    c=Column('pattern', String(100))
    c.create(t)

    c=Column('attenuator', Float)
    c.create(t)

    c=Column('mask_name', String(100))
    c.create(t)

    c=Column('mask_position', Float)
    c.create(t)

    c=Column('ramp_rate', Float)
    c.create(t)
    c=Column('ramp_duration', Float)
    c.create(t)

    c=Column('reprate', Float)
    c.create(t)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta=MetaData(bind=migrate_engine)
    t=Table('meas_ExtractionTable', meta, autoload=True)

    t.c.beam_diameter.drop()
    t.c.pattern.drop()
    t.c.mask_position.drop()
    t.c.mask_name.drop()
    t.c.attenuator.drop()
    t.c.ramp_rate.drop()
    t.c.ramp_duration.drop()
    t.c.reprate.drop()