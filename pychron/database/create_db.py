from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def session_factory(url):
    engine = create_engine(url)
    return sessionmaker(bind=engine)()



def create_db_schema(url, metadata):
    sess = session_factory(url)
    metadata.create_all(sess.bind)




if __name__ == '__main__':
    from pychron.dvc.dvc_orm import Base
    url = 'mysql+pymysql://root:DBArgon@129.138.12.160/pychronmeta'
    create_db_schema(url, Base.metadata)
