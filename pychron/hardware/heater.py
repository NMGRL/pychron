# ===============================================================================
# Copyright 2021 ross
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
from traits.api import Float, Event, Bool, Property, Int, HasTraits
from traitsui.api import View, Item, UItem, ButtonEditor, HGroup, VGroup

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.graph.stream_graph import StreamGraph
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.modbus import ModbusMixin


class HeaterMixin(HasTraits):
    setpoint = Float
    readback = Float
    onoff_button = Event
    onoff_state = Bool
    onoff_label = Property(depends_on='onoff_state')

    use_pid = Bool
    graph = Instance(StreamGraph)

    # heater interface
    def set_sepoint(self, v):
        raise NotImplementedError

    def read_setpoint(self):
        raise NotImplementedError

    def read_readback(self):
        raise NotImplementedError

    def set_active(self, state):
        raise NotImplementedError

    def set_use_pid(self, state):
        raise NotImplementedError

    def update(self):
        if self.onoff_state:
            v = self.read_readback()
            self.readback = v
            self.graph.record(v)

    def _use_pid_changed(self, v):
        self.set_use_pid(v)

    def _onoff_button_fired(self):
        self.onoff_state = not self.onoff_state
        self.set_active(self.onoff_state)

    def _get_onoff_label(self):
        return 'Off' if self.onoff_state else 'On'

    def _graph_default(self):
        g = StreamGraph()
        g.new_plot(ytitle='Readback', xtitle='Time (s)')
        g.new_series()
        return g

    def heater_view(self):
        v = View(VGroup(HGroup(UItem('name'),
                               UItem('onoff_button',
                                     editor=ButtonEditor(name='onoff_label'))),
                        HGroup(Item('setpoint'),
                               UItem('readback', editor=LCDEditor(height=30))),
                        UItem('graph', style='custom')))
        return v


class PLC2000Heater(CoreDevice, ModbusMixin, HeaterMixin):
    setpoint_address = Int
    readback_address = Int
    use_pid_address = Int
    enable_address = Int

    def load_additional_args(self, config):
        self.set_attribute(config, 'setpoint_address', 'Register', 'setpoint', cast='int')
        self.set_attribute(config, 'readback_address', 'Register', 'readback', cast='int')
        self.set_attribute(config, 'use_pid_address', 'Register', 'use_pid', cast='int')
        self.set_attribute(config, 'enable_address', 'Register', 'enable', cast='int')
        return True

    def set_sepoint(self, v):
        self._write_register(self.setpoint_address, v)

    def read_setpoint(self):
        pass

    def set_active(self, state):
        self._write_coil(self.enable_address, bool(state))

    def set_use_pid(self, state):
        self._write_coil(self.use_pid_address, bool(state))

    @get_float()
    def read_readback(self):
        resp = self._read_holding_registers(self.readback_address)
        return resp
# ============= EOF =============================================
