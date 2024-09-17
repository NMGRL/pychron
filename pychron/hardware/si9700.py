# ===============================================================================
# Copyright 2023 Jake Ross
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
import string
from traits.api import Float
from traitsui.api import VGroup, Item, UItem

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.hardware import get_float
from pychron.hardware.base_cryo_controller import BaseCryoController


class SI9700Controller(BaseCryoController):
    scan_func = "update"
    setpoint = Float
    readback = Float

    def update(self, **kw):
        self.readback = self._read_input(1)
        return self.readback

    def initialize(self, *args, **kw):
        self.communicator.write_terminator = "\r"
        return True

    def setpoints_achieved(self, setpoints, tol=1):
        return True

    def set_setpoints(self, *setpoints, block=False, delay=1):
        self.ask(f"SET {setpoints[0]}")

    def _write_setpoint(self, v, *args, **kw):
        self.ask(f"SET {v}")

    def _read_setpoint(self, output, verbose=False):
        resp = self.ask("SET?")
        if resp:
            cmd, value = resp.split(" ")
            return value.strip()

    @get_float(default=0)
    def _read_input(self, ch, **kw):
        if isinstance(ch, int):
            ch = "AB"[ch - 1]

        ch = ch.upper()
        resp = self.ask(f"T{ch}?")
        if resp:
            cmd, value = resp.split(" ")
            return value.strip()

    def get_control_group(self):
        grp = VGroup(
            Item("setpoint"),
            UItem(
                "readback",
                editor=LCDEditor(width=120, height=30),
                style="readonly",
            ),
        )
        return grp


# ============= EOF =============================================
