"""modify fittable

Revision ID: 23d790125442
Revises: 379048749428
Create Date: 2014-01-25 12:56:01.424382

"""

# revision identifiers, used by Alembic.
from sqlalchemy.orm import sessionmaker

revision = '23d790125442'
down_revision = '379048749428'

from alembic import op
import sqlalchemy as sa

def execute_sql(sql):
    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    session.execute(sql)
    session.commit()
    session.close()


def upgrade():
    op.add_column('proc_FitTable',sa.Column('error_type',sa.String(40)))

    sql = """
        update proc_FitTable as f
        set f.fit='average', error_type='SD'
        where f.fit='average_SD'
    """
    execute_sql(sql)

    sql = """
        update proc_FitTable as f
        set f.fit='average', error_type='SEM'
        where f.fit='average_SEM'
    """
    execute_sql(sql)


def downgrade():
    sql = """
        update proc_FitTable as f
        set f.fit='average_SD'
        where f.fit='average' and error_type='SD'
    """
    execute_sql(sql)

    sql = """
        update proc_FitTable as f
        set f.fit='average_SEM'
        where f.fit='average' and error_type='SEM'
    """
    execute_sql(sql)

    op.drop_column('proc_FitTable','error_type')
