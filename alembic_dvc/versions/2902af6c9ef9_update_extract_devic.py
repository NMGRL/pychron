"""update extract device

Revision ID: 2902af6c9ef9
Revises: 3874acf6600c
Create Date: 2015-07-06 08:01:22.197951

"""

# revision identifiers, used by Alembic.
from sqlalchemy.orm import sessionmaker

revision = '2902af6c9ef9'
down_revision = '3874acf6600c'

from alembic import op


def execute_sql(sql):
    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    session.execute(sql)

    session.commit()
    session.close()


def upgrade():
    sql = '''insert into ExtractDeviceTbl (name) Select distinct(AnalysisTbl.extract_device) from AnalysisTbl'''
    execute_sql(sql)
    # op.drop_column('AnalysisTbl', 'extract_device')
    op.create_foreign_key(
        "analysistbl_ibfk_3", "AnalysisTbl",
        "ExtractDeviceTbl", ["extract_device"], ["name"])


def downgrade():
    op.drop_constraint('analysistbl_ibfk_3', 'AnalysisTbl', type_='foreignkey')
