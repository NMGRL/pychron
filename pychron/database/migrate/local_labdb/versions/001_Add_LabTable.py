from sqlalchemy import *
from migrate import *
meta = MetaData()
bt = Table('LabTable', meta,
Column('id', Integer, primary_key=True),
Column('labnumber', Integer),
Column('aliquot', Integer),
Column('collection_path', BLOB),
Column('repository_path', BLOB),
Column('create_date', DateTime)
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    bt.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    bt.drop()
