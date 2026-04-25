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

# ============= enthought library imports =======================

# ============= local library imports  ==========================
import time

# ============= standard library imports ========================
from traits.api import Bool

from pychron.hardware.core.core_device import CoreDevice


class GPActuator(CoreDevice):
    invert = Bool(False)
    _lock = None

    def load_additional_args(self, config, **kw):
        self.set_attribute(config, "invert", "General", "invert", cast="boolean")
        return True

    def get_lock_state(self, *args, **kw):
        pass

    def get_indicator_state(self, obj, *args, **kw):
        return self.get_channel_state(obj, **kw)

    def get_state_word(self):
        return

    def get_channel_state(self, *args, **kw):
        """ """
        raise NotImplementedError

    def close_channel(self, obj, excl=False):
        """
        Close the channel
        obj: valve object

        return True if actuation completed successfully
        """
        return self.actuate(obj, "Close")

    def open_channel(self, obj):
        """
        Open the channel
        obj: valve object

        return True if actuation completed successfully
        """
        return self.actuate(obj, "Open")

    def actuate(self, obj, action):
        if self._lock:
            self.debug(f"{self._lock} lock acquire")
            self._lock.acquire()
            self.debug("lock acquired")

        if self._actuate(obj, action):
            ret = self._check_actuate(obj, action)
            if self._lock:
                self._lock.release()
            return ret

        if self._lock:
            self._lock.release()

    def _check_actuate(self, obj, action):
        if not obj.check_actuation_enabled:
            return True

        if obj.check_actuation_delay:
            time.sleep(obj.check_actuation_delay)

        # state = action == 'Open'
        result = self.get_indicator_state(obj, action)
        self.debug("check actuate action={}, result={}".format(action, result))

        if action == "Close":
            result = not result

        return result

    def _actuate(self, obj, action):
        raise NotImplementedError


# ============= EOF ====================================
