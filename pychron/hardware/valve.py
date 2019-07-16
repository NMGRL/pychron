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
from traits.api import Str, Float, Int, Property, Bool
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

    check_actuation_enabled = Bool(True)
    check_actuation_delay = Float(0)  # time to delay before checking actuation

    cycle_period = Float(1)
    cycle_n = Int(10)
    sample_period = Float(1)

    prefix_name = 'VALVE'

    def _software_locked(self):
        self.info('{}({}) software locked'.format(self.name, self.description))

    def _get_display_state(self):
        return 'Open' if self.state else 'Close'

    def _get_display_software_lock(self):
        return 'Yes' if self.software_lock else 'No'

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

