# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
import os
# ============= standard library imports ========================
import pickle
# ============= local library imports  ==========================
from pychron.globals import globalv
from pychron.loggable import Loggable


def load_persistence_dict(p):
    if os.path.isfile(p):
        with open(p, 'r') as rfile:
            try:
                return pickle.load(rfile)
            except (pickle.PickleError, EOFError):
                pass


def dump_persistence_dict(p, d):
    with open(p, 'w') as wfile:
        pickle.dump(d, wfile)


def load_persistence_values(obj, p, attrs):
    d = load_persistence_dict(p)
    for ai in attrs:
        try:
            setattr(obj, ai, d[ai])
        except:
            pass


def dump_persistence_values(obj, p, attrs):
    d = {ai: getattr(obj, ai) for ai in attrs}
    dump_persistence_dict(p, d)


class PersistenceMixin(object):
    pattributes = None

    def get_attributes(self):
        attrs = self.pattributes
        try:
            dattrs = tuple(self.traits(dump=True).keys())
            if attrs:
                attrs += dattrs
            else:
                attrs = dattrs
        except AttributeError, e:
            print 'ddddd', e
            pass

        return attrs

    def get_persistence_path(self):
        try:
            return self._make_persistence_path(self.persistence_path)
        except (AttributeError, NotImplementedError):
            self.warning('persistence path not implemented')

    def load(self, verbose=False):
        attrs = self.get_attributes()
        if not attrs:
            raise NotImplementedError

        if verbose:
            self.debug('***************** loading')

        p = self.get_persistence_path()
        self.debug(p)
        if p and os.path.isfile(p):
            self.debug('loading {}'.format(p))
            d = None
            with open(p, 'r') as rfile:
                try:
                    d = pickle.load(rfile)
                except (pickle.PickleError, EOFError, BaseException):
                    self.warning('Invalid pickle file {}'.format(p))
            if d:
                if verbose:
                    self.debug('***************** loading pickled object')

                for k in attrs:
                    try:
                        v = d[k]
                        if verbose:
                            self.debug('setting {} to {}'.format(k, v))
                        setattr(self, k, v)
                    except KeyError:
                        pass

    def dump(self, verbose=False):
        attrs = self.get_attributes()
        if not attrs:
            raise NotImplementedError

        p = self.get_persistence_path()
        if p:

            if verbose:
                self.debug('***************** dumping')
                d = {}
                for a in attrs:
                    v = getattr(self, a)
                    self.debug('dump {}="{}"'.format(a, v))
                    d[a] = v
            else:
                d = {a: getattr(self, a) for a in attrs}
            with open(p, 'w') as wfile:
                pickle.dump(d, wfile)

    def _make_persistence_path(self, p):
        return '{}.{}'.format(p, globalv.username)

    def warning(self, *args, **kw):
        pass

    def debug(self, *args, **kw):
        pass

    def info(self, *args, **kw):
        pass


class PersistenceLoggable(Loggable, PersistenceMixin):
    pass

# ============= EOF =============================================
