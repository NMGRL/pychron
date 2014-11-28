# ===============================================================================
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
# ===============================================================================



#============= enthought library imports =======================

#============= standard library imports ========================

#============= local library imports  ==========================
from actuator import Actuator


class ValveController(Actuator):
    def get_open_indicator_state(self, *args, **kw):
        """
        """
        if self._cdevice is not None:
            return self._cdevice.get_open_indicator_state(*args, **kw)

    def get_closed_indicator_state(self, *args, **kw):
        """
        """
        if self._cdevice is not None:
            return self._cdevice.get_close_indicator_state(*args, **kw)

#
#    def get_hard_lock_indicator_state(self, *args, **kw):
#        '''
#        '''
#        if self._cdevice is not None:
#            return self._cdevice.get_hard_lock_indicator_state(*args, **kw)
#============= EOF ====================================
