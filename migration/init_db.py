import os
import sys
import sqlalchemy as sa

root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)


def init_db(url):

    engine=sa.create_engine(url)

    from pychron.database.orms.isotope.util import Base

    meta=Base.metadata

    meta.create_all(bind=engine)

    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(os.path.join(root,"alembic.ini"))
    command.stamp(alembic_cfg, "head")

if __name__ =='__main__':
    url='mysql+pymysql://root:Argon@localhost/isotopedb_alembic?connect_timeout=3'
    #url='mysql+pymysql://root:Argon@localhost/pychrondata_minnabluff?connect_timeout=3'
    init_db(url)