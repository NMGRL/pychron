# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# =============enthought library imports=======================
import sys

from traits.api import Password, Bool, Str, on_trait_change, Any, Property, cached_property

# =============standard library imports ========================
from sqlalchemy import create_engine, distinct, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError, StatementError, \
    DBAPIError, OperationalError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
import os
import weakref
# =============local library imports  ==========================
from pychron.database.core.query import compile_query
from pychron.loggable import Loggable
from pychron.database.core.base_orm import AlembicVersionTable
from pychron import version


ATTR_KEYS = ['kind', 'username', 'host', 'name', 'password']


class SessionCTX(object):
    """
    Session Context Manager.
    This object is rarely used directly. It is mostly called by ``DatabaseAdapter.session_ctx()``

    - enter. initialize sess
    - exit. nothing, commit, or rollback

    """
    _close_at_exit = True
    _commit = True
    _parent = None

    def __init__(self, sess=None, commit=True, parent=None):
        """
        :param sess: existing Session object
        :param commit: commit Session at exit
        :param parent: DatabaseAdapter instance

        """
        self._sess = sess
        self._commit = commit
        self._parent = parent
        if sess:
            self._close_at_exit = False

    def __enter__(self):
        if self._parent:
            if self._sess is None:
                self._sess = self._parent.session_factory()

            self._parent.sess_stack += 1
            self._parent.sess = self._sess

        return self._sess

    def __exit__(self, *args, **kw):
        if self._parent:
            self._parent.sess_stack -= 1
            if not self._parent.sess_stack:
                self._parent.sess = None

        # print 'exit',self._commit, self._close_at_exit#, self._parent._sess_stack
        # self._sess.flush()
        if self._close_at_exit:
            try:
                # self._parent.debug('$%$%$%$%$%$%$%$ commit {}'.format(self._commit))
                if self._commit:
                    self._sess.commit()
                else:
                    self._sess.rollback()

            except Exception, e:
                # print 'exception commiting session: {}'.format(e)
                if self._parent:
                    self._parent.debug('$%$%$%$%$%$%$%$ commiting changes error:\n{}'.format(str(e)[:50]))
                self._sess.rollback()
            finally:
                self._sess.close()
                del self._sess


class DatabaseAdapter(Loggable):
    """
    The DatabaseAdapter is a base class for interacting with a SQLAlchemy database.
    Two main subclasses are used by pychron, IsotopeAdapter and MassSpecDatabaseAdapter.

    This class provides attributes for describing the database url, i.e host, user, password etc,
    and methods for connecting and opening database sessions.

    It also provides some helper functions used extensively by the subclasses, e.g. ``_add_item``,
    ``_retrieve_items``

    """
    sess = None

    sess_stack = 0
    reraise = False

    connected = Bool(False)
    kind = Str  # ('mysql')
    prev_kind = Str
    username = Str  # ('root')
    host = Str  # ('localhost')
    # name = Str#('massspecdata_local')
    password = Password  # ('Argon')

    # selector_klass = Any
    # selector = Any

    session_factory = None

    application = Any

    test_func = 'get_migrate_version'
    version_func = 'get_migrate_version'

    autoflush = False
    # name used when writing to database
    # save_username = Str
    connection_parameters_changed = Bool

    url = Property(depends_on='connection_parameters_changed')
    datasource_url = Property(depends_on='connection_parameters_changed')

    path = Str
    echo = False
    verbose_retrieve_query = False
    verbose = True
    connection_error = Str

    # def __init__(self, *args, **kw):
    #     super(DatabaseAdapter, self).__init__(*args, **kw)

    def create_all(self, metadata):
        """
        Build a database schema with the current connection

        :param metadata: SQLAchemy MetaData object
        """
        # if self.kind == 'sqlite':
        with self.session_ctx() as sess:
            metadata.create_all(sess.bind)

    def session_ctx(self, sess=None, commit=True):
        """
        Make a new session context.

        :return: ``SessionCTX``
        """
        if sess is None:
            sess = self.sess
        return SessionCTX(sess, parent=self, commit=commit)

    @property
    def enabled(self):
        return self.kind in ['mysql', 'sqlite', 'postgresql']

    @property
    def save_username(self):
        from pychron.globals import globalv

        return globalv.username

    @on_trait_change('username,host,password,name,kind,path')
    def reset_connection(self):
        """
        Trip the ``connection_parameters_changed`` flag. Next ``connect`` call with use the new values
        """
        self.connection_parameters_changed = True

    # @caller
    def connect(self, test=True, force=False, warn=True, version_warn=False, attribute_warn=False):
        """
        Connect to the database

        :param test: Test the connection by running ``test_func``
        :param force: Test connection even if connection parameters haven't changed
        :param warn: Warn if the connection test fails
        :param version_warn: Warn if database/pychron versions don't match
        :return: True if connected else False
        :rtype: bool
        """
        self.connection_error = ''
        if force:
            self.debug('forcing database connection')
            # self.reset()
        # self.session_factory = None

        if self.connection_parameters_changed:
            force = True

        #        print not self.isConnected() or force, self.connection_parameters_changed

        if not self.connected or force:
            self.connected = True if self.kind == 'sqlite' else False
            if self.kind == 'sqlite':
                test = False

            self.connection_error = 'Database "{}" kind not set. ' \
                                    'Set in Preferences. current kind="{}"'.format(self.name, self.kind)

            if not self.enabled:
                self.warning_dialog(self.connection_error)
            else:
                url = self.url
                if url is not None:
                    self.info('{} connecting to database {}'.format(id(self), url))
                    engine = create_engine(url, echo=self.echo)
                    #                     Session.configure(bind=engine)

                    self.session_factory = sessionmaker(bind=engine, autoflush=self.autoflush)
                    if test:
                        if self.test_func:
                            self.connected = self._test_db_connection(version_warn)
                        else:
                            self.connected = True
                    else:
                        self.connected = True

                    if self.connected:
                        self.info('connected to db {}'.format(self.url))
                        self.initialize_database()
                    else:
                        self.connection_error = 'Not Connected to Database "{}".\nAccess Denied for user= {} \
host= {}\nurl= {}'.format(self.name, self.username, self.host, self.url)
                        if warn:
                            self.warning_dialog(self.connection_error)

        self.connection_parameters_changed = False
        return self.connected

    def initialize_database(self):
        pass

    def flush(self):
        """
        flush the session
        """
        if self.sess:
            try:
                self.sess.flush()
            except:
                self.sess.rollback()

    def commit(self):
        """
        commit the session
        """
        if self.sess:
            try:
                self.sess.commit()
            except:
                self.sess.rollback()

    def get_session(self):
        """
        return the current session or make a new one

        :return: Session
        """
        sess = self.sess
        if sess is None:
            sess = self.session_factory()

        return sess

    def get_migrate_version(self, **kw):
        """
        Query the AlembicVersionTable

        """
        with self.session_ctx() as s:
            # q = s.query(MigrateVersionTable)
            q = s.query(AlembicVersionTable)
            mv = q.one()
            return mv

    @cached_property
    def _get_datasource_url(self):
        if self.kind == 'sqlite':
            url = '{}:{}'.format(os.path.basename(os.path.dirname(self.path)),
                                 os.path.basename(self.path))
        else:
            url = '{}:{}'.format(self.host, self.name)
        return url

    @cached_property
    def _get_url(self):
        kind = self.kind
        password = self.password
        user = self.username
        host = self.host
        name = self.name
        if kind in ('mysql', 'postgresql'):
            if kind == 'mysql':
                # add support for different mysql drivers
                driver = self._import_mysql_driver()
                if driver is None:
                    return
            else:
                driver = 'pg8000'

            if password:
                url = '{}+{}://{}:{}@{}/{}?connect_timeout=5'.format(kind, driver, user, password, host, name)
            else:
                url = '{}+{}://{}@{}/{}?connect_timeout=5'.format(kind, driver, user, host, name)
        else:
            url = 'sqlite:///{}'.format(self.path)

        return url

    def _import_mysql_driver(self):
        try:
            '''
                pymysql
                https://github.com/petehunt/PyMySQL/
            '''
            import pymysql

            driver = 'pymysql'
        except ImportError:
            try:
                import _mysql

                driver = 'mysqldb'
            except ImportError:
                self.warning_dialog('A mysql driver was not found. Install PyMySQL or MySQL-python')
                return

        self.info('using {}'.format(driver))
        return driver

    def _test_db_connection(self, version_warn):
        with self.session_ctx():
            try:
                # connected = False
                # if self.test_func is not None:
                # self.sess = None
                #                 self.get_session()
                #                sess = self.session_factory()
                self.info('testing database connection {}'.format(self.test_func))
                ver = getattr(self, self.test_func)(reraise=True)
                if version_warn:
                    ver = ver.version_num
                    aver = version.__alembic__
                    self.debug('testing database versions current={} local={}'.format(ver, aver))
                    if ver != aver:
                        if not self.confirmation_dialog(
                                'Your database is out of date and it may not work correctly with '
                                'this version of Pychron. Contact admin to update db.\n\n'
                                'Current={} Yours={}\n\n'
                                'Continue with Pychron despite out of date db?'.format(ver, aver)):
                            self.application.stop()
                            sys.exit()

                connected = True
            except Exception, e:
                print 'exception', e

                self.warning('connection failed to {}'.format(self.url))
                connected = False

            finally:
                self.info('closing test session')
                # if self.sess is not None:
                #                     self.sess.close()

        return connected

    def test_version(self):
        if self.version_func:
            with self.session_ctx():
                ver = getattr(self, self.version_func)()
                ver = ver.version_num
                aver = version.__alembic__
                if ver != aver:
                    return 'Database is out of data. Pychron ver={}, Database ver={}'.format(aver, ver)
                    # @deprecated

    # def _get_query(self, klass, join_table=None, filter_str=None, sess=None,
    #                     *args, **clause):
    # #         sess = self.get_session()
    #         q = sess.query(klass)
    #
    #         if join_table is not None:
    #             q = q.join(join_table)
    #
    #         if filter_str:
    #             q = q.filter(filter_str)
    #         else:
    #             q = q.filter_by(**clause)
    #         return q
    #
    #     def _get_tables(self):
    #         pass

    def _add_item(self, obj):
        #         sess = self._session
        sess = self.get_session()
        if sess:
            sess.add(obj)
            try:

                if self.autoflush:
                    sess.flush()
                return obj
            except SQLAlchemyError, e:
                import traceback
                # traceback.print_exc()
                self.debug('add_item exception {} {}'.format(obj, traceback.format_exc()))
                sess.rollback()
                if self.reraise:
                    raise

                    #     def _add_item(self, obj, sess=None):

                    #         def func(s):
                    #             s.add(obj)
                    #
                    #         if sess is None:
                    #             with session() as sess:
                    #                 func(sess)
                    #         else:
                    #             func(sess)

                    #         with session(sess) as s:
                    #             s.add(obj)
                    #         sess = self.get_session()
                    #         if sess is not None:
                    #             sess.add(obj)


    def _add_unique(self, item, attr, name):
        nitem = getattr(self, 'get_{}'.format(attr))(name)
        if nitem is None:  # or isinstance(nitem, (str, unicode)):
            self.info('adding {}= {}'.format(attr, name))
            self._add_item(item)
            nitem = item

        return nitem

    def _get_path_keywords(self, path, args):
        n = os.path.basename(path)
        r = os.path.dirname(path)
        args['root'] = r
        args['filename'] = n
        return args

    def _delete_item(self, value, name=None):
        # sess = self.sess
        # if sess is None:
        #     if self.session_factory:
        #         sess = self.session_factory()

        with self.session_ctx() as sess:
            if name is not None:
                func = getattr(self, 'get_{}'.format(name))
                item = func(value)
            else:
                item = value

            self.debug('deleting value={},name={},item={}'.format(value, name, item))
            if item:
                sess.delete(item)

    def _retrieve_items(self, table,
                        joins=None,
                        filters=None,
                        limit=None, order=None,
                        distinct_=False,
                        query_hook=None,
                        reraise=False,
                        func='all',
                        group_by=None,
                        verbose_query=False):

        sess = self.sess
        if sess is None:
            if self.session_factory:
                sess = self.session_factory()

        with self.session_ctx(sess):
            #         print 'get items', sess, self.session_factory
            #         sess = self.get_session()
            #    if sess is not None:
            if distinct_:
                if isinstance(distinct_, bool):
                    q = sess.query(distinct(table))
                else:
                    q = sess.query(distinct(distinct_))
            elif isinstance(table, tuple):
                q = sess.query(*table)
            else:
                q = sess.query(table)

            if joins:
                # print joins
                # joins = list(set(joins))
                # print joins
                try:
                    for ji in joins:
                        if ji != table:
                            q = q.join(ji)
                except InvalidRequestError:
                    if reraise:
                        raise

            if filters is not None:
                for fi in filters:
                    q = q.filter(fi)

            if order is not None:
                if not isinstance(order, tuple):
                    order = (order, )
                q = q.order_by(*order)

            if group_by is not None:
                if not isinstance(order, tuple):
                    group_by = (group_by, )
                q = q.group_by(*group_by)

            if limit is not None:
                q = q.limit(limit)

            if query_hook:
                q = query_hook(q)

            if verbose_query or self.verbose_retrieve_query:
                # print compile_query(q)
                self.debug(compile_query(q))

            return self._query(q, func, reraise)

    def _retrieve_first(self, table, value=None, key='name', order_by=None):
        if value is not None:
            if not isinstance(value, (str, int, unicode, long, float)):
                return value

        # sess = self.sess
        # if sess is None:
        #     if self.session_factory:
        #         sess = self.session_factory()

        with self.session_ctx() as sess:
            q = sess.query(table)
            if value is not None:
                q = q.filter(getattr(table, key) == value)

            try:
                if order_by is not None:
                    q = q.order_by(order_by)
                return q.first()
            except SQLAlchemyError, e:
                print 'execption first', e
                return

    def _query_all(self, q, **kw):
        ret = self._query(q, 'all', **kw)
        return ret or []

    def _query_first(self, q, **kw):
        return self._query(q, 'first', **kw)

    def _query_one(self, q, **kw):
        q = q.limit(1)
        return self._query(q, 'one', **kw)

    # @conditional_caller
    def _query(self, q, func, reraise=False, verbose_query=False):
        if verbose_query:
            self.debug(compile_query(q))

        # print compile_query(q)
        f = getattr(q, func)
        try:
            return f()
        except SQLAlchemyError, e:
            if reraise:
                raise
                # if self.verbose:
                #     self.debug('_query exception {}'.format(e))
                # import traceback
                # traceback.print_exc()
                # self.sess.rollback()

    def _retrieve_item(self, table, value, key='name', last=None,
                       joins=None, filters=None, options=None, verbose=True,
                       verbose_query=False):
        #         sess = self.get_session()
        #         if sess is None:
        #             return
        if not isinstance(value, (str, int, unicode, long, float, list, tuple)):
            return value

        if not isinstance(value, (list, tuple)):
            value = (value,)

        if not isinstance(key, (list, tuple)):
            key = (key,)

        def __retrieve(s):
            q = s.query(table)

            #             if options:
            #                 q = q.options(subqueryload(options))

            if joins:
                try:
                    for ji in joins:
                        if ji != table:
                            q = q.join(ji)
                except InvalidRequestError:
                    pass

            if filters is not None:
                for fi in filters:
                    q = q.filter(fi)

            for k, v in zip(key, value):
                q = q.filter(getattr(table, k) == v)

            if last:
                q = q.order_by(last)

            if verbose_query or self.verbose_retrieve_query:
                self.debug(compile_query(q))

            ntries = 3
            import traceback

            for i in range(ntries):
                try:
                    return q.one()
                except (DBAPIError, OperationalError, StatementError):
                    self.debug(traceback.format_exc())
                    s.rollback()
                    continue
                except MultipleResultsFound:
                    if verbose:
                        self.debug(
                            'multiples row found for {} {} {}. Trying to get last row'.format(table.__tablename__, key,
                                                                                              value))
                    try:
                        if hasattr(table, 'id'):
                            q = q.order_by(table.id.desc())
                        return q.limit(1).all()[-1]

                    except (SQLAlchemyError, IndexError, AttributeError), e:
                        if verbose:
                            self.debug('no rows for {} {} {}'.format(table.__tablename__, key, value))
                        break

                except NoResultFound:
                    if verbose and self.verbose:
                        self.debug('no row found for {} {} {}'.format(table.__tablename__, key, value))
                    break

        # no longer true: __retrieve is recursively called if a StatementError is raised
        # use retry loop instead
        with self.session_ctx() as sess:
            return __retrieve(sess)


    # @deprecated
    def _get_items(self, table, gtables,
                   join_table=None, filter_str=None,
                   limit=None,
                   order=None,
                   key=None
    ):

        if isinstance(join_table, str):
            join_table = gtables[join_table]

        q = self._get_query(table, join_table=join_table,
                            filter_str=filter_str)
        if order:
            for o in order \
                    if isinstance(order, list) else [order]:
                q = q.order_by(o)

        if limit:
            q = q.limit(limit)

        # reorder based on id
        if order:
            q = q.from_self()
            q = q.order_by(table.id)

        res = q.all()
        if key:
            return [getattr(ri, key) for ri in res]
        return res

    # def selector_factory(self, **kw):
    #     sel = self._selector_factory(**kw)
    #     self.selector = weakref.ref(sel)()
    #     return self.selector
    #
    # def _selector_default(self):
    #     return self._selector_factory()
    #
    # def _selector_factory(self, **kw):
    #     if self.selector_klass:
    #         s = self.selector_klass(db=self, **kw)
    #         #            s.load_recent()
    #         return s


class PathDatabaseAdapter(DatabaseAdapter):
    path_table = None

    def add_path(self, rec, path, **kw):
        if self.path_table is None:
            raise NotImplementedError
        kw = self._get_path_keywords(path, kw)
        p = self.path_table(**kw)
        rec.path = p
        return p


class SQLiteDatabaseAdapter(DatabaseAdapter):
    kind = 'sqlite'

    def build_database(self):
        self.connect(test=False)
        if not os.path.isfile(self.path):
            with self.session_ctx() as sess:
                meta = MetaData()
                self._build_database(sess, meta)

    def _build_database(self, sess, meta):
        raise NotImplementedError

# ============= EOF =============================================