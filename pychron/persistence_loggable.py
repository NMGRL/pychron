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
#============= local library imports  ==========================
from pychron.globals import globalv
from pychron.loggable import Loggable


class PersistenceMixin(object):
    pattributes = None

    def get_persistence_path(self):
        try:
            return self._make_persistence_path(self.persistence_path)
        except (AttributeError, NotImplementedError):
            self.warning('persistence path not implemented')

    def load(self):
        self.debug('***************** loading')
        if not self.pattributes:
            raise NotImplementedError

        p = self.get_persistence_path()
        self.debug('{} {}'.format(p, os.path.isfile(p)))
        if p and os.path.isfile(p):
            d = None
            with open(p, 'r') as fp:
                try:
                    d = pickle.load(fp)
                except (pickle.PickleError, EOFError):
                    self.warning('Invalid pickle file {}'.format(p))
            if d:
                self.debug('***************** loading has d')
                for k in self.pattributes:
                    try:
                        v = d[k]
                        self.debug('setting {} to {}'.format(k, v))
                        setattr(self, k, v)
                    except KeyError:
                        pass

    def dump(self, verbose=False):
        if not self.pattributes:
            raise NotImplementedError

        p = self.get_persistence_path()
        if p:

            if verbose:
                self.debug('***************** dumping')
                d = {}
                for a in self.pattributes:
                    v = getattr(self, a)
                    self.debug('dump {}="{}"'.format(a, v))
                    d[a] = v
            else:
                d = {a: getattr(self, a) for a in self.pattributes}
            with open(p, 'w') as fp:
                pickle.dump(d, fp)

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

#============= EOF =============================================

