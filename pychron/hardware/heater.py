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
from traits.api import Float, Event, Bool, Property, Int, HasTraits, Instance
from traitsui.api import View, Item, UItem, ButtonEditor, HGroup, VGroup

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.graph.stream_graph import StreamGraph
from pychron.hardware import get_float, get_boolean
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.modbus import ModbusMixin


class HeaterMixin(HasTraits):
    setpoint = Float(enter_set=True, auto_set=False)
    readback = Float
    onoff_button = Event
    onoff_state = Bool
    onoff_label = Property(depends_on="onoff_state")

    use_pid = Bool
    graph = Instance(StreamGraph)

    def load_from_device(self):
        self.debug('finish loading heater. initialize with values from device')
        self.setpoint = self.read_setpoint()
        self.readback = self.read_readback()
        self.use_pid = self.read_use_pid()
        self.onoff_state = self.read_onoff_state()
        return True

    # heater interface
    def _setpoint_changed(self, new):
        self.set_setpoint(new)

    def set_setpoint(self, v):
        raise NotImplementedError

    def read_use_pid(self):
        raise NotImplementedError

    def read_onoff_state(self):
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
            if v is not None:
                self.readback = v
                self.graph.record(v)

    def _use_pid_changed(self, v):
        self.debug("set use_pid={}".format(v))
        self.set_use_pid(v)

    def _onoff_button_fired(self):
        self.onoff_state = not self.onoff_state
        self.debug("set state = {}".format(self.onoff_state))
        self.set_active(self.onoff_state)

    def _get_onoff_label(self):
        return "Off" if self.onoff_state else "On"

    def _graph_default(self):
        g = StreamGraph()
        g.new_plot(ytitle="Readback", xtitle="Time (s)")
        g.new_series()
        return g

    def heater_view(self):
        v = View(
            VGroup(
                HGroup(
                    UItem("name", style="readonly"),
                    Item("use_pid", label="Use PID"),
                    UItem(
                        "onoff_button", editor=ButtonEditor(label_value="onoff_label")
                    ),
                ),
                HGroup(
                    Item("setpoint"),
                    UItem("readback", editor=LCDEditor(width=100, height=30)),
                ),
                UItem("graph", style="custom"),
            )
        )
        return v


class PLC2000Heater(CoreDevice, ModbusMixin, HeaterMixin):
    setpoint_address = Int
    readback_address = Int
    use_pid_address = Int
    enable_address = Int

    def load_additional_args(self, config):
        self.set_attribute(
            config, "setpoint_address", "Register", "setpoint", cast="int"
        )
        self.set_attribute(
            config, "readback_address", "Register", "readback", cast="int"
        )
        self.set_attribute(config, "use_pid_address", "Register", "use_pid", cast="int")
        self.set_attribute(config, "enable_address", "Register", "enable", cast="int")
        self.debug("Automatically do coil_address = address-1")

        for attr in ("setpoint", "readback", "use_pid", "enable"):
            attr = "{}_address".format(attr)
            v = getattr(self, attr)
            setattr(self, attr, v - 1)

        return True

    def set_setpoint(self, v):
        if self.setpoint_address is not None:
            self.debug("set setpoint addr={}, {}".format(self.setpoint_address, v))
            self._write_int(self.setpoint_address, v)
        else:
            self.debug("setpoint_address not set")

    def set_active(self, state):
        if self.enable_address is not None:
            self.debug(
                "set active addr={}, {}".format(self.enable_address, bool(state))
            )
            self._write_coil(self.enable_address, bool(state))
        else:
            self.debug("enable_address not set")

    def set_use_pid(self, state):
        if self.use_pid_address is not None:
            self.debug(
                "set use pid addr={}, {}".format(self.use_pid_address, bool(state))
            )
            self._write_coil(self.use_pid_address, bool(state))
        else:
            self.debug("use_pid_address not set")

    @get_float()
    def read_readback(self):
        if self.readback_address is not None:
            v = self._read_input_float(self.readback_address)
            self.debug("read readback addr={}, {}".format(self.readback_address, v))
            return v
        else:
            self.debug("readback address not set")

    @get_boolean()
    def read_use_pid(self):
        if self.use_pid_address:
            rr = self._read_coils(self.use_pid_address)
            return rr.bits[0]
        else:
            self.debug("use_pid address not set")

    @get_boolean()
    def read_onoff_state(self):
        if self.enable_address is not None:
            rr = self._read_coils(self.enable_address)
            return rr.bits[0]
        else:
            self.debug("enable address not set")

    @get_float()
    def read_setpoint(self):
        if self.setpoint_address is not None:
            return self._read_input_float(self.setpoint_address)
        else:
            self.debug("setpoint address not set")


# ============= EOF =============================================
