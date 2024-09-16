# ===============================================================================
# Copyright 2024 ross
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
import os
import time

import yaml
from traits.api import (
    Int,
    List,
    HasTraits,
    Bool,
    Property,
    Color,
    CInt,
    observe,
    Str,
    File,
    Float,
    Button,
    Instance,
)
from traitsui.group import HGroup
from traitsui.item import UItem
from traitsui.view import View

from pychron.core.helpers.filetools import glob_list_directory
from pychron.hardware import get_float, get_boolean
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.modbus import ModbusMixin
from pychron.persistence_loggable import PersistenceMixin


class BakeoutChannel(HasTraits):
    temperature = Float
    duty_cycle = Float
    setpoint = Float

    temperature_address = CInt
    duty_cycle_address = CInt
    setpoint_address = CInt
    reset_address = CInt
    pid_enable_address = CInt
    ramp_enable_address = CInt
    pid_mode_address = CInt

    ramp_setpoint_address = (
        CInt  # represents an array of 3 values. this is the start modbus address
    )
    ramp_time_address = CInt
    ramp_soak_address = CInt

    overtemp_highhigh_address = CInt
    overtemp_ishighhigh_address = CInt
    clear_overtemp_address = CInt

    enabled = Bool(False)
    display = Bool(True)
    clear_overtemp = Button

    shortname = Property
    name = Property
    index = Int
    color = Color("red")
    tag = Str

    def _get_name(self):
        return f"Channel {self.index+1}"

    def _get_shortname(self):
        return f"CH. {self.index+1}"

    def coil_address(self, attr):
        return getattr(self, f"{attr}_address") - 1

    def ramp_step_address(self, attr, step):
        return (getattr(self, f"ramp_{attr}_address") - 1) + (step * 2)

    def traits_view(self):
        v = View(
            HGroup(
                UItem("enabled"),
                UItem("shortname", style="readonly"),
                UItem("temperature", style="readonly"),
                UItem("color"),
            )
        )
        return v


class BakeoutPLC(CoreDevice, ModbusMixin, PersistenceMixin):
    channels = List(BakeoutChannel)
    configuration = File
    configurations = List

    persistence_name = "bakeout"
    pattributes = ("configuration",)

    selected_channel = Instance("BakeoutChannel")

    # def load(self, verbose=True):
    #     CoreDevice.load(self)
    #     return super().load()
    def prepare_destroy(self):
        PersistenceMixin.dump(self)

    def load_additional_args(self, config):
        for s in config.sections():
            if s.startswith("Channel"):
                ch = BakeoutChannel()
                ch.index = int(s.split(" ")[1]) - 1
                for opt in config.options(s):
                    setattr(ch, opt, config.get(s, opt))
                self.channels.append(ch)

        for p in glob_list_directory(
            self.bakeout_configuration_dir, extension=".yaml", remove_extension=True
        ):
            self.configurations.append(p)

        PersistenceMixin.load(self)
        return True

    @property
    def bakeout_configuration_dir(self):
        return os.path.dirname(self.config_path)

    def set_overtemp_alarm(self, ch):
        yd = self.get_channel_configuration(ch)
        self._write_int(
            ch.coil_address("overtemp_highhigh"), yd.get("overtemp_highhigh", 300)
        )

    def set_ramp_values(self, ch):
        p = os.path.join(self.bakeout_configuration_dir, f"{self.configuration}.yaml")
        # with open(p, 'r') as f:
        #     yd = yaml.load(f, Loader=yaml.FullLoader)
        #     print(ch.tag, yd)
        #     yd = next((v for k,v  in yd.items() if k == ch.tag), None)
        yd = self.get_channel_configuration(ch)
        for i in range(3):
            for tag in ("setpoint", "time", "soak"):
                self._write_float(ch.ramp_step_address(tag, i), yd[tag][i])

    def get_channel_configuration(self, ch):
        p = os.path.join(self.bakeout_configuration_dir, f"{self.configuration}.yaml")
        with open(p, "r") as f:
            yd = yaml.load(f, Loader=yaml.FullLoader)
            yd = next((v for k, v in yd.items() if k == ch.tag), None)
            return yd

    @observe("configuration")
    def handle_configuration(self, event):
        for ch in self.channels:
            self.set_ramp_values(ch)

    @observe("channels.items.clear_overtemp")
    def handle_clear_overtemp(self, event):
        ch = event.object
        ret = self._write_coil(ch.coil_address("clear_overtemp"), True)
        print("clear overtemp", ch.clear_overtemp_address, ret)
        time.sleep(0.1)
        ret = self._write_coil(ch.coil_address("clear_overtemp"), False)
        print("clear overtemp", ch.clear_overtemp_address, ret)

    @observe("channels.items.enabled")
    def handle_channel_enable(self, event):
        print("handle channel enable", event)

        ch = event.object

        flag = event.new
        if flag:
            self.set_ramp_values(ch)
            self.set_overtemp_alarm(ch)

        # enable PID
        ret = self._write_coil(ch.coil_address("pid_enable"), flag)
        print("enable PID", ch.pid_enable_address, ret)

        # # # enable Ramp
        # ret = self._write_coil(ch.ramp_enable_address-1, flag)
        # print('enable ramp', ch.ramp_enable_address, ret)

        # # go to Auto mode
        ret = self._write_coil(ch.coil_address("pid_mode"), flag)
        print("mode", ch.pid_mode_address, ret)

        # reset the Ramp
        ret = self._write_coil(ch.coil_address("reset"), True)
        print("reseta", ch.reset_address, ret)

        ret = self._write_coil(ch.coil_address("reset"), False)
        print("resetb", ch.reset_address, ret)

    @get_float()
    def read_temperature(self, channel=0):
        ch = self.channels[channel]
        t = self._read_input_float(ch.coil_address("temperature"))
        ch.temperature = t
        return t

    @get_float()
    def read_duty_cycle(self, channel=0):
        ch = self.channels[channel]
        dc = self._read_float(ch.coil_address("duty_cycle"))
        ch.duty_cycle = dc
        return dc

    @get_float()
    def read_setpoint(self, channel=0):
        ch = self.channels[channel]
        f = self._read_float(ch.coil_address("setpoint"))
        ch.setpoint = f
        return f

    @get_boolean()
    def read_overtemp_ishighhigh(self, channel=0):
        ch = self.channels[channel]
        result = self._read_coils(ch.coil_address("overtemp_ishighhigh"))
        b = result.bits[0]
        if b:
            ch.enabled = False
        return b


# ============= EOF =============================================
