#===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Int
import cPickle as pickle
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.helpers.datetime_tools import generate_datetimestamp

class PipetteTracker(Loggable):
    inner = Str
    outer = Str
    counts = Int
    _shot_loaded = False
#     def __init__(self, *args, **kw):
#         super(PipetteTracker, self).__init__(*args, **kw)
#         self.load()

    def check_shot(self, name):
        '''
            check shot called only when valve opens
        '''
        if name == self.inner:
            self._shot_loaded = True
            return True

        elif name == self.outer:
            if self._shot_loaded:
                self._increment()
                self._shot_loaded = False
                return True

    def _increment(self):

        self.counts += 1

        self.debug('increment shot count {}'.format(self.counts))
        self.dump()

#===============================================================================
# persistence
#===============================================================================
    def load(self):
        p = self._get_path_id()
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    params = pickle.load(fp)
                    self._load(params)
                except (pickle.PickleError, OSError):
                    pass

    def dump(self):
        p = self._get_path_id()
        with open(p, 'w') as fp:
            pickle.dump(self._dump(), fp)
            self.debug('saved current shot count {}'.format(self.counts))

    def _load(self, params):
        if params:
            try:
                cnts = params['counts']
                last_shot_time = params['last_shot_time']
            except KeyError:
                cnts = 0

            self.counts = cnts
            self.debug('loaded current shot count {} time:{}'.format(self.counts,
                                                                     last_shot_time
                                                                     ))

    def _dump(self):
        d = dict(
               counts=self.counts,
               last_shot_time=generate_datetimestamp()
               )

        return d

    def _get_path_id(self):
        return os.path.join(paths.hidden_dir, 'pipette-{}_{}'.format(self.inner, self.outer))

#============= EOF =============================================
