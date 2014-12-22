# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Str, Any, Bool, Property

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class Switch(Loggable):
    display_name = Str
    address = Str
    actuator = Any
    state = Bool(False)
    description = Str
    query_state = Bool(True)
    software_lock = Bool(False)
    enabled = Bool(True)

    actuator_name = Property(depends_on='actuator')
    prefix_name = 'SWITCH'
    parent = Str
    parent_inverted = Bool(False)

    def __init__(self, name, *args, **kw):
        """
        """
        self.display_name = name
        kw['name'] = '{}-{}'.format(self.prefix_name, name)
        super(Switch, self).__init__(*args, **kw)

    def get_hardware_state(self):
        """
        """
        result = None
        if self.actuator is not None:
            result = self.actuator.get_channel_state(self)
            if isinstance(result, bool):
                self.set_state(result)
            else:
                result = False

        return result

    def get_lock_state(self):
        if self.actuator:
            return self.actuator.get_lock_state(self)

    def set_state(self, state):
        self.state = state

    def set_open(self, mode='normal'):
        self.info('open mode={}'.format(mode))
        #        current_state = copy(self.state)
        state_change = False
        success = True
        if self.software_lock:
            self._software_locked()
        else:
            success = self._open_()
            if success:
                if not self.state:
                    state_change = True
                self.state = True

        return success, state_change

    def set_closed(self, mode='normal'):
        self.info('close mode={}'.format(mode))
        #        current_state = copy(self.state)
        state_change = False
        success = True
        if self.software_lock:
            self._software_locked()
        else:
            #            print 'pre state', self.state, current_state
            success = self._close_()
            if success:
                #                print 'self.state',self.state, current_state
                if self.state == True:
                    state_change = True
                self.state = False

        return success, state_change

    def lock(self):
        self.software_lock = True

    def unlock(self):
        self.software_lock = False

    def _open_(self, mode='normal'):
        """
        """
        actuator = self.actuator
        r = True
        if mode == 'debug':
            r = True
        elif self.actuator is not None:
            if mode.startswith('client'):
                # always actuate if mode is client
                r = True if actuator.open_channel(self) else False
            else:
                # dont actuate if already open
                if self.state:
                    r = True
                else:
                    r = True if actuator.open_channel(self) else False

            if actuator.simulation:
                r = True
        return r

    def _close_(self, mode='normal'):
        """
        """
        r = True
        actuator = self.actuator
        if mode == 'debug':
            r = True

        elif actuator is not None:
            if mode.startswith('client'):
                print 'close', self.state
                r = True if actuator.close_channel(self) else False
            else:
                # dont actuate if already closed
                if not self.state:
                    r = True
                else:
                    r = True if actuator.close_channel(self) else False

            if actuator.simulation:
                r = True
        return r

    def _get_actuator_name(self):
        name = ''
        if self.actuator:
            name = self.actuator.name
        return name

# ============= EOF =============================================

