"""add time_zero_offset to fits

Revision ID: 534de5290781
Revises: 2a203d447c9c
Create Date: 2014-04-16 09:13:37.348430

"""

# revision identifiers, used by Alembic.

revision = '534de5290781'
down_revision = '2a203d447c9c'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker


def upgrade():
    op.add_column('proc_FitTable',
                  sa.Column('time_zero_offset', sa.Float))
    sql = """
        update
        proc_FitTable as ft
        set ft.time_zero_offset=0
        where ft.time_zero_offset is NULL
    """

    # engine = create_engine('mysql://alexander:@localhost/alembic_content_migration_example')
    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    session.execute(sql)
    session.commit()
    session.close()


def downgrade():
    op.drop_column('proc_FitTable', 'time_zero_offset')
