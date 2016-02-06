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
from traits.api import Str, Any, Float, Int, Property, Bool
from traitsui.api import View, Item, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.switch import Switch


class HardwareValve(Switch):
    """
    """
    display_name = Str
    display_state = Property(depends_on='state')
    display_software_lock = Property(depends_on='software_lock')

    #moved to switch
    # address = Str
    # actuator = Any
    # state = Bool(False)
    # actuator_name = Property(depends_on='actuator')
    # query_state = Bool(True)
    # description = Str
    # software_lock = Bool(False)
    # enabled = Bool(True)

    check_actuation_enabled = Bool(True)
    check_actuation_delay = Float(0)  # time to delay before checking actuation

    cycle_period = Float(1)
    cycle_n = Int(10)
    sample_period = Float(1)

    evalve = Any
    prefix_name = 'VALVE'

    # def is_name(self, name):
    #     if len(name) == 1:
    #         name = '{}-{}'.format(self.prefix_name, name)
    #     return name == self.name

    def _state_changed(self):
        if self.evalve:
            self.evalve.state = self.state

    def _software_lock_changed(self):
        if self.evalve:
            self.evalve.soft_lock = self.software_lock

    def _software_locked(self):
        self.info('{}({}) software locked'.format(self.name, self.description))

    #    def _get_shaft_low(self):
    #        if self.canvas_valve:
    #            return self.canvas_valve.low_side.orientation
    #
    #    def _get_shaft_high(self):
    #        if self.canvas_valve:
    #            return self.canvas_valve.high_side.orientation

    #    def _get_position(self):
    #        if self.canvas_valve:
    #            return ','.join(map(str, self.canvas_valve.translate))

    def _get_display_state(self):
        return 'Open' if self.state else 'Close'

    def _get_display_software_lock(self):
        return 'Yes' if self.software_lock else 'No'

    # def _get_actuator_name(self):
    #     name = ''
    #     if self.actuator:
    #         name = self.actuator.name
    #     return name

    def traits_view(self):
        info = VGroup(
            Item('display_name', label='Name', style='readonly'),
            Item('display_software_lock', label='Locked', style='readonly'),
            Item('address', style='readonly'),
            Item('actuator_name', style='readonly'),
            Item('display_state', style='readonly'),
            show_border=True,
            label='Info')
        sample = VGroup(
            Item('sample_period', label='Period (s)'),
            label='Sample',
            show_border=True)
        cycle = VGroup(
            Item('cycle_n', label='N'),
            Item('sample_period', label='Period (s)'),
            label='Cycle',
            show_border=True)
        geometry = VGroup(
            Item('position', style='readonly'),
            #                          Item('shaft_low', style='readonly'),
            #                          Item('shaft_high', style='readonly'),
            label='Geometry',
            show_border=True)
        return View(
            VGroup(info, sample, cycle, geometry),

            #                    buttons=['OK', 'Cancel'],
            title='{} Properties'.format(self.name))

# ============= EOF ====================================
#    def open(self, mode='normal'):
#        '''
#
#        '''
#        self._state_change = False
#        self.info('open mode={}'.format(mode))
#        self.debug = mode == 'debug'
#        self._fsm.Open()
#
# #        if mode in ['auto', 'manual', 'debug', 'remote']:
# #            self._fsm.Open()
#
#        result = self.success
#        if self.error is not None:
#            result = self.error
#            self.error = None
#
#        if not result:
#            pass
#            #self._fsm.RClose()
#
#        return result, self._state_change
#
#    def close(self, mode='normal'):
#        '''
#
#        '''
#        self._state_change = False
#        self.info('close mode={}'.format(mode))
#
#        self.debug = mode == 'debug'
# #        if mode in ['auto', 'manual', 'debug', 'remote']:
# #            self._fsm.Close()
#        self._fsm.Close()
#
#        result = self.success
#        if self.error is not None:
#            result = self.error
#            self.error = None
#
#        if not result:
#            pass
#            #self._fsm.ROpen()
#
#        return result, self._state_change

#    def acquire_critical_section(self):
#        self._critical_section = True
#
#    def release_system_lock(self):
#        self._critical_section = False
#
#    def isCritical(self):
#        return self._critical_section
#    def _error_(self, message):
#        self.error = message
#        self.warning(message)

#    def warning(self, msg):
#        '''
#            @type msg: C{str}
#            @param msg:
#        '''
# #        super(HardwareValve, self).warning(msg)
#        Loggable.warning(self, msg)
#        self.success = False
#    def get_hard_lock(self):
#        '''
#        '''
#        if self.actuator is not None:
#            r = self.actuator.get_hard_lock_indicator_state(self)
#        else:
#            r = False
#
#        return r
#
#    def get_hard_lock_indicator_state(self):
#        '''
#        '''
#
#        s = self.get_hardware_state()
#        r = self.get_hard_lock()
#
#        if r:
#            if s:
#                self._fsm.HardLockOpen()
#            else:
#                self._fsm.HardLockClose()
#        else:
#            self._fsm.HardUnLock()
#        #print self.auto
#        return r
