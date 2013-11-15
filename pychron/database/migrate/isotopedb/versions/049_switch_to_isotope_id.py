from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_FitTable', meta, autoload=True)
    try:
        t.c.isotope.drop()
    except:
        pass

    c = Column('isotope_id', Integer)
    try:
        c.create(t)
    except:
        pass

    tt = Table('meas_IsotopeTable', meta, autoload=True)
    cons = ForeignKeyConstraint([t.c.isotope_id], [tt.c.id])
    cons.create()
#

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)

    tt = Table('meas_IsotopeTable', meta, autoload=True)

    t = Table('proc_FitTable', meta, autoload=True)

    cons = ForeignKeyConstraint([t.c.isotope_id], [tt.c.id])
    cons.drop()

    try:
        t.c.isotope_id.drop()
    except:
        pass

#    c = Column('isotope', String(80))
#    c.create(t)
