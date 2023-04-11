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
from __future__ import absolute_import
from __future__ import print_function

import os
import pickle

from pychron.loggable import Loggable
from pychron.paths import paths


def load_persistence_dict(p):
    if os.path.isfile(p):
        with open(p, "r") as rfile:
            try:
                return pickle.load(rfile)
            except (pickle.PickleError, EOFError):
                pass


def dump_persistence_dict(p, d):
    with open(p, "w") as wfile:
        pickle.dump(d, wfile)


def load_persistence_values(obj, p, attrs):
    d = load_persistence_dict(p)
    for ai in attrs:
        try:
            setattr(obj, ai, d[ai])
        except BaseException:
            pass


def dump_persistence_values(obj, p, attrs):
    d = {ai: getattr(obj, ai) for ai in attrs}
    dump_persistence_dict(p, d)


def dumpable(klass, *args, **kw):
    return klass(dump=True, *args, **kw)


class PersistenceMixin(object):
    pattributes = None
    persistence_name = None

    def get_attributes(self):
        attrs = self.pattributes
        try:
            dattrs = tuple(self.traits(dump=True).keys())
            if attrs:
                attrs += dattrs
            else:
                attrs = dattrs
        except AttributeError as e:
            print("ddddd", e)
            pass

        return attrs

    @property
    def persistence_path(self):
        if not self.persistence_name:
            raise NotImplementedError

        return os.path.join(paths.hidden_dir, self.persistence_name)

    def get_persistence_path(self):
        try:
            return self._make_persistence_path(self.persistence_path)
        except (AttributeError, NotImplementedError) as e:
            print(e)
            self.warning("persistence path not implemented")

    def load(self, verbose=True):
        attrs = self.get_attributes()
        if not attrs:
            raise NotImplementedError

        if verbose:
            self.debug("***************** loading")

        p = self.get_persistence_path()
        self.debug(p)
        if p and os.path.isfile(p):
            self.debug("loading {}".format(p))
            d = None
            with open(p, "rb") as rfile:
                try:
                    d = pickle.load(rfile)
                except (pickle.PickleError, EOFError, BaseException):
                    self.warning("Invalid pickle file {}".format(p))
            if d:
                if verbose:
                    self.debug("***************** loading pickled object")

                for k in attrs:
                    try:
                        v = d[k]
                        if verbose:
                            self.debug("setting {} to {}".format(k, v))
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
                self.debug("***************** dumping")
                d = {}
                for a in attrs:
                    v = getattr(self, a)
                    self.debug('dump {}="{}"'.format(a, v))
                    d[a] = v
            else:
                d = {a: getattr(self, a) for a in attrs}
            with open(p, "wb") as wfile:
                pickle.dump(d, wfile)

    def _make_persistence_path(self, p):
        return p
        # return '{}.{}'.format(p, globalv.username)

    def warning(self, *args, **kw):
        pass

    def debug(self, *args, **kw):
        pass

    def info(self, *args, **kw):
        pass


class PersistenceLoggable(Loggable, PersistenceMixin):
    pass


# ============= EOF =============================================
