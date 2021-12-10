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
import os
from datetime import datetime, timedelta
from threading import Lock

import six
from sqlalchemy import create_engine, distinct, MetaData
from sqlalchemy.exc import (
    SQLAlchemyError,
    InvalidRequestError,
    StatementError,
    DBAPIError,
    OperationalError,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from traits.api import (
    Password,
    Bool,
    Str,
    on_trait_change,
    Any,
    Property,
    cached_property,
    Int,
)

from pychron.database.core.base_orm import AlembicVersionTable
from pychron.database.core.query import compile_query
from pychron.loggable import Loggable
from pychron.regex import IPREGEX


def obscure_host(h):
    if IPREGEX.match(h):
        h = "x.x.x.{}".format(h.split(".")[-1])
    return h


def binfunc(ds, hours):
    ds = [dx.timestamp for dx in ds]
    p1 = ds[0]
    delta_seconds = hours * 3600
    td = timedelta(seconds=delta_seconds * 0.25)

    for i, di in enumerate(ds):
        i = max(0, i - 1)

        dd = ds[i]
        if (di - dd).total_seconds() > delta_seconds:
            yield p1 - td, dd + td
            p1 = di

    yield p1 - td, di + td


class SessionCTX(object):
    def __init__(self, parent, use_parent_session=True):
        self._use_parent_session = use_parent_session
        self._parent = parent
        self._session = None
        self._psession = None

    def __enter__(self):
        if self._parent:
            if self._use_parent_session:
                self._parent.create_session()
                return self._parent.session
            else:
                self._psession = self._parent.session
                self._session = self._parent.session_factory()
                self._parent.session = self._session
                return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            self._session.close()
        else:
            self._parent.close_session()

        if self._psession:
            self._parent.session = self._psession
        self._psession = None


class MockQuery:
    def join(self, *args, **kw):
        return self

    def filter(self, *args, **kw):
        # type: (object, object) -> object
        return self

    def all(self, *args, **kw):
        return []

    def order_by(self, *args, **kw):
        return self


class MockSession:
    def query(self, *args, **kw):
        return MockQuery()

    # def __getattr__(self, item):
    #     return


class DatabaseAdapter(Loggable):
    """
    The DatabaseAdapter is a base class for interacting with a SQLAlchemy database.
    Two main subclasses are used by pychron, IsotopeAdapter and MassSpecDatabaseAdapter.

    This class provides attributes for describing the database url, i.e host, user, password etc,
    and methods for connecting and opening database sessions.

    It also provides some helper functions used extensively by the subclasses, e.g. ``_add_item``,
    ``_retrieve_items``

    """

    session = None

    sess_stack = 0
    reraise = False

    connected = Bool(False)
    kind = Str
    prev_kind = Str
    username = Str
    host = Str
    password = Password
    timeout = Int

    session_factory = None

    application = Any

    test_func = "get_versions"
    version_func = "get_versions"

    autoflush = True
    autocommit = False
    commit_on_add = True

    # name used when writing to database
    # save_username = Str
    connection_parameters_changed = Bool

    url = Property(depends_on="connection_parameters_changed")
    datasource_url = Property(depends_on="connection_parameters_changed")

    path = Str
    echo = False
    verbose_retrieve_query = False
    verbose = True
    connection_error = Str
    _session_lock = None

    modified = False
    _trying_to_add = False
    _test_connection_enabled = True

    def __init__(self, *args, **kw):
        super(DatabaseAdapter, self).__init__(*args, **kw)
        self._session_lock = Lock()

    def create_all(self, metadata):
        """
        Build a database schema with the current connection

        :param metadata: SQLAchemy MetaData object
        """
        # if self.kind == 'sqlite':
        metadata.create_all(self.session.bind)

    # def session_ctx(self, sess=None, commit=True, rollback=True):
    #     """
    #     Make a new session context.
    #
    #     :return: ``SessionCTX``
    #     """
    #     with self._session_lock:
    #         if sess is None:
    #             sess = self.sess
    #         return SessionCTX(sess, parent=self, commit=commit, rollback=rollback)

    _session_cnt = 0

    def session_ctx(self, use_parent_session=True):
        with self._session_lock:
            return SessionCTX(self, use_parent_session)

    def create_session(self, force=False):
        if self.connect(test=False):
            if self.session_factory:
                if force:
                    self.debug("force create new session {}".format(id(self)))
                    if self.session:
                        self.session.close()

                    self.session = self.session_factory()
                    self._session_cnt = 1
                else:
                    if not self.session:
                        # self.debug('create new session {}'.format(id(self)))
                        self.session = self.session_factory()
                    self._session_cnt += 1
            else:
                self.warning("no session factory")
        else:
            self.session = MockSession()

    def close_session(self):
        if self.session and not isinstance(self.session, MockSession):
            self.session.flush()

            self._session_cnt -= 1
            if not self._session_cnt:
                self.debug("close session {}".format(id(self)))
                self.session.close()
                self.session = None

    @property
    def enabled(self):
        return self.kind in ["mysql", "sqlite", "postgresql", "mssql"]

    @property
    def save_username(self):
        from pychron.globals import globalv

        return globalv.username

    @on_trait_change("username,host,password,name,kind,path")
    def reset_connection(self):
        """
        Trip the ``connection_parameters_changed`` flag. Next ``connect`` call with use the new values
        """
        self.connection_parameters_changed = True
        self.session_factory = None
        self.session = None

    # @caller
    def connect(
        self, test=True, force=False, warn=True, version_warn=True, attribute_warn=False
    ):
        """
        Connect to the database

        :param test: Test the connection by running ``test_func``
        :param force: Test connection even if connection parameters haven't changed
        :param warn: Warn if the connection test fails
        :param version_warn: Warn if database/pychron versions don't match
        :return: True if connected else False
        :rtype: bool
        """
        self.connection_error = ""
        if force:
            self.debug("forcing database connection")

        if self.connection_parameters_changed:
            self._test_connection_enabled = True
            force = True

        if not self.connected or force:
            # self.connected = True if self.kind == 'sqlite' else False
            self.connected = False
            pool_recycle = 600
            if self.kind == "sqlite":
                self.connected = True
                test = False
                pool_recycle = -1

            self.connection_error = (
                'Database "{}" kind not set. '
                'Set in Preferences. current kind="{}"'.format(self.name, self.kind)
            )

            if not self.enabled:
                from pychron.core.ui.gui import invoke_in_main_thread

                invoke_in_main_thread(self.warning_dialog, self.connection_error)
            else:
                url = self.url
                if url is not None:
                    self.info(
                        "{} connecting to database {}".format(id(self), self.public_url)
                    )
                    engine = create_engine(
                        url, echo=self.echo, pool_recycle=pool_recycle
                    )

                    self.session_factory = sessionmaker(
                        bind=engine,
                        autoflush=self.autoflush,
                        expire_on_commit=False,
                        autocommit=self.autocommit,
                    )
                    if test:
                        if not self._test_connection_enabled:
                            warn = False
                        else:
                            if self.test_func:
                                self.connected = self._test_db_connection(version_warn)
                            else:
                                self.connected = True
                    else:
                        self.connected = True

                    if self.connected:
                        self.info("connected to db {}".format(self.public_url))
                        # self.initialize_database()
                    else:
                        self.connection_error = 'Not Connected to Database "{}".\nAccess Denied for user= {} \
host= {}\nurl= {}'.format(
                            self.name, self.username, self.host, self.public_url
                        )
                        if warn:
                            from pychron.core.ui.gui import invoke_in_main_thread

                            invoke_in_main_thread(
                                self.warning_dialog, self.connection_error
                            )

        self.connection_parameters_changed = False
        return self.connected

    # def initialize_database(self):
    # pass

    def rollback(self):
        if self.session:
            self.session.rollback()

    def flush(self):
        """
        flush the session
        """
        if self.session:
            try:
                self.session.flush()
            except:
                self.session.rollback()

    def expire(self, i):
        if self.session:
            self.session.expire(i)

    def expire_all(self):
        if self.session:
            self.session.expire_all()

    def commit(self):
        """
        commit the session
        """
        if self.session:
            try:
                self.session.commit()
            except BaseException as e:
                self.warning("Commit exception: {}".format(e))
                self.session.rollback()

    def delete(self, obj):
        if self.session:
            self.session.delete(obj)

    def post_commit(self):
        if self._trying_to_add:
            self.modified = True

    def add_item(self, *args, **kw):
        return self._add_item(*args, **kw)

    # def get_session(self):
    #     """
    #     return the current session or make a new one
    #
    #     :return: Session
    #     """
    #     sess = self.sess
    #     if sess is None:
    #         self.debug('$$$$$$$$$$$$$$$$ session is None')
    #         sess = self.session_factory()
    #
    #     return sess

    def get_migrate_version(self, **kw):
        """
        Query the AlembicVersionTable

        """
        q = self.session.query(AlembicVersionTable)
        mv = q.one()
        return mv

    def get_versions(self, **kw):
        pass

    @property
    def public_datasource_url(self):
        if self.kind == "sqlite":
            url = "{}:{}".format(
                os.path.basename(os.path.dirname(self.path)),
                os.path.basename(self.path),
            )
        else:

            url = "{}:{}".format(obscure_host(self.host), self.name)
        return url

    @cached_property
    def _get_datasource_url(self):
        if self.kind == "sqlite":
            url = "{}:{}".format(
                os.path.basename(os.path.dirname(self.path)),
                os.path.basename(self.path),
            )
        else:
            url = "{}:{}".format(self.host, self.name)
        return url

    @property
    def public_url(self):
        kind = self.kind
        user = self.username
        host = self.host
        name = self.name
        if kind == "sqlite":
            pu = "{}:{}".format(
                os.path.basename(os.path.dirname(self.path)),
                os.path.basename(self.path),
            )
        else:
            pu = "{}://{}@{}/{}".format(kind, user, host, name)

        return pu

    @cached_property
    def _get_url(self):
        kind = self.kind
        password = self.password
        user = self.username
        host = self.host
        name = self.name
        timeout = self.timeout

        if kind in ("mysql", "postgresql", "mssql"):
            if kind == "mysql":
                # add support for different mysql drivers
                driver = self._import_mysql_driver()
                if driver is None:
                    return
            elif kind == "mssql":
                driver = self._import_mssql_driver()
                if driver is None:
                    return
            else:
                driver = "pg8000"

            if password:
                user = "{}:{}".format(user, password)

            prefix = "{}+{}://{}@".format(kind, driver, user)

            if driver == "pyodbc":
                url = "{}{}".format(prefix, name)
            else:
                url = "{}{}/{}".format(prefix, host, name)
                if kind == "mysql" and self.timeout:
                    url = "{}?connect_timeout={}".format(url, timeout)

        else:
            url = "sqlite:///{}".format(self.path)

        return url

    def _import_mssql_driver(self):
        driver = None
        try:
            import pyodbc

            driver = "pyodbc"

        except ImportError:
            try:
                import pymssql

                driver = "pymssql"
            except ImportError:
                pass

        self.info('using mssql driver="{}"'.format(driver))
        return driver

    def _import_mysql_driver(self):

        try:
            """
            pymysql
            https://github.com/petehunt/PyMySQL/
            """
            import pymysql

            driver = "pymysql"
        except ImportError:
            try:
                import _mysql

                driver = "mysqldb"
            except ImportError:
                self.warning_dialog(
                    "A mysql driver was not found. Install PyMySQL or MySQL-python"
                )
                return

        self.info('using mysql driver="{}"'.format(driver))
        return driver

    def _test_db_connection(self, version_warn):
        self.connected = True
        self.create_session()

        try:
            self.info("testing database connection {}".format(self.test_func))
            getattr(self, self.test_func)(reraise=True)
            if version_warn:
                self._version_warn_hook()

            connected = True
        except OperationalError:
            self.warning("Operational connection failed to {}".format(self.public_url))
            connected = False
            self._test_connection_enabled = False

        except Exception as e:
            self.debug_exception()
            self.warning(
                "connection failed to {} exception={}".format(self.public_url, e)
            )
            connected = False

        finally:
            self.info("closing test session")
        self.close_session()

        return connected

    def _version_warn_hook(self):
        pass

    # def test_version(self):
    #     ver = getattr(self, self.version_func)()
    #     ver = ver.version_num
    #     aver = version.__alembic__
    #     if ver != aver:
    #         return 'Database is out of data. Pychron ver={}, Database ver={}'.format(aver, ver)

    def _add_item(self, obj):
        sess = self.session
        if sess:
            sess.add(obj)
            try:
                if self.autoflush:
                    sess.flush()
                    self.modified = True

                self._trying_to_add = True
                if not self.autocommit and self.commit_on_add:
                    sess.commit()

                return obj
            except SQLAlchemyError as e:
                import traceback

                self.debug(
                    "add_item exception {} {}".format(obj, traceback.format_exc())
                )
                sess.rollback()
                if self.reraise:
                    raise
        else:
            self.critical("No session")

    def _add_unique(self, item, attr, name):
        nitem = getattr(self, "get_{}".format(attr))(name)
        if nitem is None:
            self.info("adding {}= {}".format(attr, name))
            self._add_item(item)
            nitem = item

        return nitem

    def _get_date_range(self, q, asc, desc, hours=0):
        lan = q.order_by(asc).first()
        han = q.order_by(desc).first()

        lan = datetime.now() if not lan else lan.timestamp
        han = datetime.now() if not han else han.timestamp
        td = timedelta(hours=hours)

        return lan - td, han + td

    def _delete_item(self, value, name=None):
        if name is not None:
            func = getattr(self, "get_{}".format(name))
            item = func(value)
        else:
            item = value

        if item:
            self.debug("deleting value={},name={},item={}".format(value, name, item))
            self.session.delete(item)

    def _retrieve_items(
        self,
        table,
        joins=None,
        filters=None,
        limit=None,
        order=None,
        distinct_=False,
        query_hook=None,
        reraise=False,
        func="all",
        group_by=None,
        verbose_query=False,
    ):

        sess = self.session
        if sess is None or isinstance(sess, MockSession):
            self.debug("USING MOCKSESSION************** {}".format(sess))
            return []

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
                order = (order,)
            q = q.order_by(*order)

        if group_by is not None:
            if not isinstance(order, tuple):
                group_by = (group_by,)
            q = q.group_by(*group_by)

        if limit is not None:
            q = q.limit(limit)

        if query_hook:
            q = query_hook(q)

        if verbose_query or self.verbose_retrieve_query:
            # print compile_query(q)
            self.debug(compile_query(q))

        items = self._query(q, func, reraise)
        if items is None:
            items = []
        return items

    def _retrieve_first(self, table, value=None, key="name", order_by=None):
        if value is not None:
            if not isinstance(value, (str, int, six.text_type, int, float)):
                return value
        q = self.session.query(table)
        if value is not None:
            q = q.filter(getattr(table, key) == value)

        try:
            if order_by is not None:
                q = q.order_by(order_by)
            return q.first()
        except SQLAlchemyError as e:
            print("execption first", e)
            return

    def _query_all(self, q, **kw):
        ret = self._query(q, "all", **kw)
        return ret or []

    def _query_first(self, q, **kw):
        return self._query(q, "first", **kw)

    def _query_one(self, q, **kw):
        q = q.limit(1)
        return self._query(q, "one", **kw)

    def _query(self, q, func, reraise=False, verbose_query=False):
        if verbose_query:
            try:
                cq = compile_query(q)
                self.debug(cq)
            except BaseException:
                cq = "Query failed to compile"
                self.debug_exception()

        # print compile_query(q)
        f = getattr(q, func)
        try:
            return f()
        except NoResultFound:
            if verbose_query:
                self.info("no results found for query -- {}".format(cq))
        except OperationalError as e:
            self.debug("_query operation exception")
            self.debug_exception()

        except SQLAlchemyError as e:
            if self.verbose:
                self.debug("_query exception {}".format(e))

            try:
                self.rollback()
                self.reset_connection()
                self.connect()
            except BaseException:
                pass

            if reraise:
                raise e

    def _append_filters(self, f, kw):

        filters = kw.get("filters", [])
        if isinstance(f, (tuple, list)):
            filters.extend(f)
        else:
            filters.append(f)
        kw["filters"] = filters
        return kw

    def _append_joins(self, f, kw):
        joins = kw.get("joins", [])
        if isinstance(f, (tuple, list)):
            joins.extend(f)
        else:
            joins.append(f)
        kw["joins"] = joins
        return kw

    def _retrieve_item(
        self,
        table,
        value,
        key="name",
        last=None,
        joins=None,
        filters=None,
        options=None,
        verbose=True,
        verbose_query=False,
    ):

        if not isinstance(value, (str, int, six.text_type, int, float, list, tuple)):
            return value

        if not isinstance(value, (list, tuple)):
            value = (value,)

        if not isinstance(key, (list, tuple)):
            key = (key,)

        def __retrieve(s):
            q = s.query(table)

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
                            "multiples row found for {} {} {}. Trying to get last row".format(
                                table.__tablename__, key, value
                            )
                        )
                    try:
                        if hasattr(table, "id"):
                            q = q.order_by(table.id.desc())
                        return q.limit(1).all()[-1]

                    except (SQLAlchemyError, IndexError, AttributeError) as e:
                        if verbose:
                            self.debug(
                                "no rows for {} {} {}".format(
                                    table.__tablename__, key, value
                                )
                            )
                        break

                except NoResultFound:
                    if verbose and self.verbose:
                        self.debug(
                            "no row found for {} {} {}".format(
                                table.__tablename__, key, value
                            )
                        )
                    break

        close = False
        if self.session is None:
            self.create_session()
            close = True

        ret = __retrieve(self.session)

        if close:
            self.close_session()
        return ret

    def _get_items(
        self,
        table,
        gtables,
        join_table=None,
        filter_str=None,
        limit=None,
        order=None,
        key=None,
    ):

        if isinstance(join_table, str):
            join_table = gtables[join_table]

        q = self._get_query(table, join_table=join_table, filter_str=filter_str)
        if order:
            for o in order if isinstance(order, list) else [order]:
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


class PathDatabaseAdapter(DatabaseAdapter):
    path_table = None

    def add_path(self, rec, path, **kw):
        if self.path_table is None:
            raise NotImplementedError
        kw = self._get_path_keywords(path, kw)
        p = self.path_table(**kw)
        rec.path = p
        return p

    def _get_path_keywords(self, path, args):
        n = os.path.basename(path)
        r = os.path.dirname(path)
        args["root"] = r
        args["filename"] = n
        return args


class SQLiteDatabaseAdapter(DatabaseAdapter):
    kind = "sqlite"

    def build_database(self):
        self.connect(test=False)
        if not os.path.isfile(self.path):
            meta = MetaData()
            self._build_database(self.session, meta)

    def _build_database(self, sess, meta):
        raise NotImplementedError

        # ============= EOF =============================================
