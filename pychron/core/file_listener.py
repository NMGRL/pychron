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

# ============= enthought library imports =======================
# ============= standard library imports ========================
from threading import Thread
import time
import os
# ============= local library imports  ==========================

class FileListener(object):
    _path = None
    _callback = None
    _check_callback = None
    _alive = False
    _freq = None

    def __init__(self, path, callback=None, check=None, freq=1):
        """
            two methods for check if the file has changed
            1. check=None
                a file has changed if its modified time is different from the original modified time
            2. check=callable
                use a callable to compare files
                e.g experiment_set uses check_for_mods which compares the sha digests of the file contents

            freq= in hertz... sleep period =1/freq


            remember to call stop() to stop checking the file for changes
        """
        self._path = path
        self._callback = callback
        self._check_callback = check
        self._freq = freq

        self._alive = True
        if os.path.isfile(self._path):
            t = Thread(target=self._listen)
            t.start()

    @property
    def otime(self):
        return os.stat(self._path).st_mtime

    def stop(self):
        self._alive = False

    def _listen(self):
        self._otime = self.otime
        while self._alive:
            time.sleep(1 / self._freq)
            if self._check():
                self._callback()
                self._otime = self.otime

    def _check(self):
        if self._check_callback:
            return self._check_callback()
        else:
            return self.otime != self._otime


# ============= EOF =============================================
