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
from traits.api import Str, Any, Bool, Property, Float
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class BaseSwitch(Loggable):
    display_name = Str
    description = Str
    prefix_name = 'BASE_SWITCH'
    state = Bool(False)
    software_lock = Bool(False)
    enabled = Bool(True)

    def __init__(self, name, *args, **kw):
        """
        """
        self.display_name = name
        kw['name'] = '{}-{}'.format(self.prefix_name, name)
        super(BaseSwitch, self).__init__(*args, **kw)

    def set_state(self, state):
        self.state = state

    def set_open(self, *args, **kw):
        pass

    def set_closed(self, *args, **kw):
        pass

    def lock(self):
        self.software_lock = True

    def unlock(self):
        self.software_lock = False

    def get_hardware_state(self):
        pass


class ManualSwitch(BaseSwitch):
    prefix_name = 'MANUAL_SWITCH'

    def set_open(self, *args, **kw):
        self.state = True
        return True, True

    def set_closed(self, *args, **kw):
        self.state = False
        return True, True


class Switch(BaseSwitch):
    address = Str
    actuator = Any

    query_state = Bool(True)


    actuator_name = Property(depends_on='actuator')
    prefix_name = 'SWITCH'
    parent = Str
    parent_inverted = Bool(False)

    settling_time = Float(0)

    owner = Str

    def state_str(self):
        return '{}{}{}'.format(self.name, self.state, self.software_lock)

    def get_hardware_state(self, verbose=True):
        """
        """
        result = None
        if self.actuator is not None:
            result = self.actuator.get_channel_state(self, verbose=verbose)
            if isinstance(result, bool):
                self.set_state(result)
            else:
                result = False

        return result

    def get_lock_state(self):
        if self.actuator:
            return self.actuator.get_lock_state(self)

    def set_open(self, mode='normal'):
        return self._actuate_state(self._open, mode, not self.state, True)

    def set_closed(self, mode='normal'):
        return self._actuate_state(self._close, mode, self.state, False)



    def _actuate_state(self, func, mode, cur, set_value):
        """
            func: self._close, self._open
            mode: normal, client
            cur: bool, not self.state if open, self.state if close
            set_value: open-True, close-False
        """
        self.info('actuate state mode={}'.format(mode))
        state_change = False
        success = True
        if self.software_lock:
            self._software_locked()
        else:
            success = func(mode)

            if success:
                if cur:
                    state_change = True
                self.state = set_value

        return success, state_change

    def _open(self, mode='normal'):
        """
        """
        return self._act(mode, 'open_channel', not self.state)

    def _close(self, mode='normal'):
        """
        """
        return self._act(mode, 'close_channel', self.state)

    def _act(self, mode, func, do_actuation):
        """

        :param mode:
        :param func:
        :param do_actuation:
        :return:
        """
        r = True
        actuator = self.actuator
        if mode == 'debug':
            r = True

        elif actuator is not None:
            func = getattr(actuator, func)
            if mode.startswith('client'):
                r = func(self)
            else:
                if do_actuation:
                    r = func(self)
                else:
                    r = True

        if self.settling_time:
            time.sleep(self.settling_time)

        return r

    def _get_actuator_name(self):
        name = ''
        if self.actuator:
            name = self.actuator.name
        return name

# ============= EOF =============================================

