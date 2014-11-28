# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import sqlalchemy

from pychron.deprecate import  deprecated_message


#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================

@deprecated_message('use DatabaseAdapter._add_item instead')
def add(func):
    def _add(obj, *args, **kw):

        kwargs = kw.copy()
        for key in ('unique', 'commit', 'flush'):
            if kwargs.has_key(key):
                kwargs.pop(key)


        sess = obj.get_session()
        dbr = None
        if sess:
            dbr, add = func(obj, *args, **kwargs)
            if dbr and add:
                sess.add(dbr)

                if kw.has_key('flush'):
                    sess.flush()
                elif kw.has_key('commit'):
                    sess.commit()

        return dbr

    return _add

def get_first(func):
    def _get_first(obj, name, *args, **kw):
        return _getter('first', func, obj, name, *args, **kw)
    return _get_first

@deprecated_message('use DatabaseAdapter._retrieve_item instead')
def get_one(func):
    def __get_one(obj, name, *args, **kw):
        return _get_one(func, obj, name, *args, **kw)
    return __get_one

def _get_one(*args, **kw):
    return _getter('one', *args, **kw)

def _getter(getfunc, func, obj, name,
            *args, **kw):

    if name is not None and not isinstance(name, (str, int, unicode, long, float)):
        return name

    order_by = None
    params = func(obj, name, *args, **kw)
    if isinstance(params, tuple):
        if len(params) == 3:
            table, attr, order_by = params
        else:
            table, attr = params

    else:
        table = params
        attr = 'name'

    sess = obj.get_session()
    q = sess.query(table)
    if name is not None:
        q = q.filter(getattr(table, attr) == name)
    if order_by is not None:
        q = q.order_by(order_by)

#    return getattr(q, getfunc)()
    try:
        return getattr(q, getfunc)()
    except sqlalchemy.exc.SQLAlchemyError, e:
#        print 'get_one, e1', e
        try:
            q = q.order_by(table.id.desc())
            return q.limit(1).all()[-1]
        except (sqlalchemy.exc.SQLAlchemyError, IndexError, AttributeError), e:
            pass
#            print 'get_one, e2', e
#            pass

def delete_one(func):
    def _delete_one(obj, name, *args, **kw):
        sess = obj.get_session()
        dbr = _get_one(func, obj, name, *args, **kw)
        sess.delete(dbr)
        sess.commit()

    return _delete_one

def sql_retrieve(func):
    try:
        return func()
    except sqlalchemy.exc.SQLAlchemyError, e:
        pass
# ============= EOF =============================================
