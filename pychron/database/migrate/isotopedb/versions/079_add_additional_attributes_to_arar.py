from sqlalchemy import *

attrs = ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36',
         'k39', 'ca37', 'cl36', 'rad40']


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata

    meta = MetaData(bind=migrate_engine)
    t = Table('proc_ArArTable', meta, autoload=True)

    #cons = PrimaryKeyConstraint(t.c.id)
    #cons.drop()
    #t.c.id.drop()

    #c=Column('hash', String(32))
    #c.create(t, primary_key=True)
    #
    #cons = PrimaryKeyConstraint(c)

    # Create the constraint
    #cons.create()

    for ai in attrs:
        c = Column(ai, Float)
        c.create(t)

        c = Column('{}_err'.format(ai), Float)
        c.create(t)

    c = Column('age_err_wo_j', Float)
    c.create(t)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    t = Table('proc_ArArTable', meta, autoload=True)
    for ai in attrs:
        getattr(t.c, ai).drop()
        getattr(t.c, '{}_err'.format(ai)).drop()

    t.c.age_err_wo_j.drop()
    #c=t.c.hash
    #cons = PrimaryKeyConstraint(c)
    # Drop the constraint
    #cons.drop()
    #c.drop()

    #c=Column('id', Integer)
    #c.create(t, primary_key=True)
    #cons = PrimaryKeyConstraint(c)
    #cons.create()
