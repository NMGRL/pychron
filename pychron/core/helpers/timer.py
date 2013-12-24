#===============================================================================
# Copyright 2011 Jake Ross
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



#=============enthought library imports=======================
#============= standard library imports ========================
from threading import Event
import time

from PySide.QtCore import QThread
#============= local library imports  ==========================


class Timer(QThread):
    def __init__(self, period, func, delay=0, *args, **kw):
        super(Timer, self).__init__()
        self._period = period / 1000.0
        self.func = func

        self._flag = Event()
        self._flag.clear()

        self._delay = delay / 1000.0
        self._args = args
        self._kwargs = kw

        self.start()


    def run(self):

    #         p = self._period
    #         self._completed = False
        func = self.func
        flag = self._flag
        args = self._args
        kwargs = self._kwargs
        delay = self._delay

        if delay:
            flag.wait(delay)

        flag.clear()
        while not flag.isSet():
            st = time.time()
            func(*args, **kwargs)
            t = max(0, self._period - time.time() + st)
            if t:
                flag.wait(t)

    def wait_for_completion(self, timeout=None):
        st = time.time()
        while 1:
            if timeout:
                if time.time() - st > timeout:
                    return 'timeout'

            if not self.isActive():
                break
            time.sleep(0.01)

    def Stop(self):
        self._flag.set()

    stop = Stop

    def isActive(self):
        return self.isRunning() and not self.isFinished()

    #         # need to wait unit
    #         self.f
    #         return not self._flag.is_set()

    # and not self._completed

    def set_interval(self, v):
        self._period = v / 1000.

    def get_interval(self):
        '''
            return period in s
        '''
        return self._period

    #============= EOF =====================================
