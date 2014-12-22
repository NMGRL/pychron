# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
# ============= local library imports  ==========================
from PySide.QtCore import QThread
class Thread(QThread):
    _target = None
    _args = None
    _kwargs = None
    def __init__(self, name=None, target=None, args=None, kwargs=None):
        self._target = target
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

        self._args = args
        self._kwargs = kwargs
        QThread.__init__(self)
        self.setObjectName(name)

    def run(self):
        if self._target:
            self._target(*self._args, **self._kwargs)

    def join(self, timeout=None):
        if timeout:
            self.wait(timeout)
        else:
            self.wait()



def currentThreadName():
    return QThread.currentThread().objectName()

# ============= EOF =============================================
