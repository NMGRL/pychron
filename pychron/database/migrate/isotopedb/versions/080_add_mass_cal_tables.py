from sqlalchemy import *
from migrate import *

meta = MetaData()
ht = Table('spec_MassCalHistoryTable', meta,
           Column('id', Integer, primary_key=True),
           Column('create_date', DateTime),
           Column('spec_id', Integer),
)

mt = Table('spec_MassCalScanTable', meta,
           Column('id', Integer, primary_key=True),
           Column('history_id', Integer),
           Column('blob', BLOB),
           Column('center', Float),
           Column('mol_wt_id', Integer)
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    spec = Table('gen_MassSpectrometerTable', meta, autoload=True)
    mwt = Table('gen_MolecularWeightTable', meta, autoload=True)
    ht.create()
    mt.create()

    fk = ForeignKeyConstraint([ht.c.spec_id], [spec.c.id])
    fk.create()

    fk = ForeignKeyConstraint([mt.c.history_id], [ht.c.id])
    fk.create()

    fk = ForeignKeyConstraint([mt.c.mol_wt_id], [mwt.c.id])
    fk.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    spec = Table('gen_MassSpectrometerTable', meta, autoload=True)
    mwt = Table('gen_MolecularWeightTable', meta, autoload=True)

    fk = ForeignKeyConstraint([ht.c.spectrometer_id], [spec.c.id])
    fk.drop()

    fk = ForeignKeyConstraint([mt.c.history_id], [ht.c.id])
    fk.drop()

    fk = ForeignKeyConstraint([mt.c.molecular_weight_id], [mwt.c.id])
    fk.drop()

    ht.drop()
    mt.drop()