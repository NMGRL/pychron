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
from traits.api import Float, Int, Str
from traitsui.api import View, Item, UItem, HGroup, UReadonly

from pychron.core.ui.color_map_bar_editor import BarGaugeEditor
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice


class SPCIonPumpController(CoreDevice):
    scan_func = "update"

    pressure = Float

    address = Int
    display_name = Str
    low = 1e-10
    high = 1e-7
    use_checksum_validation = False

    def load_additional_args(self, config):
        self.set_attribute(config, "address", "General", "address", cast="int")
        self.set_attribute(config, "display_name", "General", "display_name")

        return True

    def update(self, *args, **kw):
        return self.get_pressure()

    def get_pressure(self):
        r = self._read_pressure()
        self.pressure = r

        return self.pressure

    @property
    def telnet_mode(self):
        return self.communicator.name.endswith("telnet")

    @get_float(0)
    def _read_pressure(self):
        cmd = self._make_command("0B")
        resp = self.ask(cmd, verbose=True)
        if resp:
            if self.telnet_mode:
                # example response OK 00 4.1E-11 Torr
                status, err, data, unit = resp.split(" ")
            else:
                addr, status, err, data, unit, chk = resp.split(" ")

            return data

    def _make_command(self, cmd):
        if self.telnet_mode:
            return f"spc {cmd}"
        else:
            a = " ".join(("~", "{:02X}".format(self.address), cmd))
            a = f"{a} "
            return f"{a} {self._calculate_checksum(a)}"

    #         a = " ".join(("~", "{:02X}".format(self.address), cmd))
    #         a = f"{a} "
    #         return f"{a} {self._calculate_checksum(a)}"

    # return "{} {}".format(a, self._calculate_checksum(a))

    def _calculate_checksum(self, a):
        if self.use_checksum_validation:
            checksum = 0
            for c in a:
                checksum += ord(c)

            checksum = checksum % 256
            checksum = f"{checksum:02X}"
        else:
            checksum = "00"
        return checksum

    def pump_view(self):
        v = View(
            HGroup(
                UReadonly(
                    "display_name",
                ),
                Item(
                    "pressure", format_str="%0.2e", show_label=False, style="readonly"
                ),
                Item(
                    "pressure",
                    show_label=False,
                    width=100,
                    editor=BarGaugeEditor(
                        low=1e-10, high=1e-7, scale="power", width=100, color_scalar=1
                    ),
                ),
            )
        )

        return v


# ============= EOF =============================================
