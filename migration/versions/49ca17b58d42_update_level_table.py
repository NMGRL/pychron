"""update level table

Revision ID: 49ca17b58d42
Revises: 52f976e8c538
Create Date: 2015-01-22 14:53:59.064931

"""

# revision identifiers, used by Alembic.

revision = '49ca17b58d42'
down_revision = '52f976e8c538'

from alembic import op
import sqlalchemy as sa
#
# def execute_sql(sql):
#     from sqlalchemy.orm import sessionmaker
#
#     Session = sessionmaker(bind=op.get_bind())
#     session = Session()
#
#     session.execute(sql)
#     session.commit()
#     session.close()


def upgrade():
    op.add_column('irrad_LevelTable', sa.Column('create_date', sa.DateTime))
    op.add_column('irrad_LevelTable', sa.Column('last_modified', sa.DateTime))
    # table = op.Operations(op.get_context())._table('irrad_LevelTable')
    # sql = create_timestamp_trigger_for_modification('irrad_LevelTable', 'modified_date')
    # execute_sql(sql)

def downgrade():
    op.drop_column('irrad_LevelTable', 'create_date')
    op.drop_column('irrad_LevelTable', 'last_modified')