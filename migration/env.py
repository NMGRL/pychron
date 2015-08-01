from __future__ import with_statement
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None
import sys, os

root = os.path.join(os.path.expanduser('~'), 'Programming/github/pychron_dev')
sys.path.append(root)

from pychron.database.orms.isotope.util import Base

target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    nver = get_revision(context)
    try:
        with context.begin_transaction():
            try:
                context.run_migrations()
            except Exception, e:
                nver=None
                raise e
    finally:
        # print context.get_head_revision()
        # print context.get_revision_argument()
        # for di in dir(context):
        #     print di
        update_pychron_version(nver)

        connection.close()


def get_revision(context):
    ctx = context.get_context()
    # for change, prev_rev, rev, doc in ctx._migrations_fn(
    #                                         ctx.get_current_revision(),
    #                                         ctx):
    #     print '00000000000000',change, prev_rev, rev, doc
    #
    changes=ctx._migrations_fn(
        ctx.get_current_revision(),
        ctx)
    if changes:
        change, prev_rev, rev, doc=changes[-1]
        return rev


def update_pychron_version(nver):
    if not nver:
        return
    from pychron import version

    temp = '''
__version__ = '{}'
__commit__ = '{}'
__alembic__ = '{}'
# ============= EOF =============================================
'''.format(version.__version__,
           version.__commit__, nver)

    # print context.get_context().opts
    # # print context.context_opts['destination_rev']
    pp = os.path.join(root, 'pychron', 'version.py')
    with open(pp, 'w') as wfile:
        wfile.write(temp)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

