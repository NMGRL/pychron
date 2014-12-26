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
import time
from traits.api import Str, Event
# ============= standard library imports ========================
from threading import Thread
from glob import glob
import os
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class DirectoryWatcher(Loggable):
    _path = Str
    _alive = False
    dir_changed = Event

    def __init__(self, path, *args, **kw):
        super(DirectoryWatcher, self).__init__(*args, **kw)
        self._path = path

    def start(self):
        self._start()

    def stop(self):
        self._alive = False

    def _start(self):
        self.info('start polling {} for changes'.format(self._path))
        self._alive = True
        t = Thread(target=self._poll)
        t.start()

    def _poll(self):
        period = 1
        while 1:
            if not self._alive:
                break
            nfiles = glob(os.path.join(self._path, '*.png'))

            if nfiles:
                self.dir_changed = nfiles

            time.sleep(period)
# ============= EOF =============================================




