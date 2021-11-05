# ===============================================================================
# Copyright 2018 ross
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

"""
Preiffer Vacuum Protocol
http://mmrc.caltech.edu/Vacuum/Pfeiffer%20Turbo/Pfeiffer%20Interface%20RS@32.pdf

TC 110 Electronic Drive Unit
http://mmrc.caltech.edu/Optical%20Furnace/Manuals/Pfeiffer%20TC%20110%20Elec.%20Drive%20Unt.pdf
"""

from traitsui.api import View, UItem, HGroup, ButtonEditor, Item
from traits.api import Float, Int, Bool, Event, Property

from pychron.core.helpers.strtools import to_bool
from pychron.core.ui.lcd_editor import LCDEditor
from pychron.hardware.OnOffMixin import OnOffMixin
from pychron.hardware.core.core_device import CoreDevice
from pychron.core.pychron_traits import BorderVGroup

import re

BASE = r"^(?P<address>\d{3})(?P<action>\d{2})(?P<parameter>\d{3})(?P<datalength>\d{2})"
RESPONSE_RE = re.compile(BASE)


def dt2(v):
    return float(v) / 100.0


PARAMETERS = {
    "set_speed": (308, int),
    "actual_speed": (309, int),
    "drive_current": (310, dt2),
    "motor_pump": (23, to_bool),
    "standby": (2, to_bool)
}


def make_pattern(dl):
    return "{}(?P<data>\d{{{}}})(?P<checksum>\d{{3}})".format(BASE, dl)


def check_checksum(resp, chksum):
    r = resp[:-3]

    print(
        "calc {} {}  {}".format(
            calc_checksum(r) == int(chksum), r, calc_checksum(r), int(chksum)
        )
    )
    return calc_checksum(r) == int(chksum)


def calc_checksum(msg):
    checksum = sum((ord(mi) for mi in msg))
    return checksum % 256


class HiPace(CoreDevice, OnOffMixin):
    scan_func = "update"

    standby = Bool
    motor_pump = Bool
    set_speed = Int
    actual_speed = Int
    drive_current = Float
    address = 1

    standby_button = Event
    standby_label = Property(depends_on="standby_state")

    onoff_state_name = 'motor_pump'

    def _get_standby_label(self):
        return "Standby On" if self.standby else "Standby Off"

    def _standby_button_fired(self):
        self.standby_state = not self.standby
        self.debug("set state = {}".format(self.standby))
        self.set_standby(self.standby)

    def _onoff_button_fired(self):
        self.onoff_state = not self.onoff_state
        self.debug("set state = {}".format(self.onoff_state))
        self.set_active(self.onoff_state)

    def update(self):
        self.debug("update")
        self.read_set_speed()
        self.read_actual_speed()
        self.read_drive_current()
        self.read_state()
        self.read_standby_state()

    def set_standby(self, state):
        self._set_parameter("standby", int(state))

    def set_active(self, state):
        self._set_parameter("motor_pump", int(state))

    def read_state(self):
        return self._read_parameter("motor_pump")

    def read_standby_state(self):
        return self._read_parameter("standby")

    def read_drive_current(self):
        return self._read_parameter("drive_current")

    def read_set_speed(self):
        return self._read_parameter("set_speed")

    def read_actual_speed(self):
        return self._read_parameter("actual_speed")

    def _set_parameter(self, attr, value, verbose=True):
        param, datatype = PARAMETERS[attr]
        cmd = self._assemble("set", param, value)
        resp = self.ask(cmd, verbose=verbose)
        raw = self._get_data(resp)
        data = datatype(raw)
        if verbose:
            self.debug("set parameter data {}={},  raw={}".format(attr, data, raw))
        return data

    def _read_parameter(self, attr, verbose=False):
        param, datatype = PARAMETERS[attr]
        cmd = self._assemble("read", param)
        resp = self.ask(cmd, verbose=verbose)
        data = self._get_data(resp)
        if verbose:
            self.debug("read parameter data {}={}".format(attr, data))
        try:
            v = datatype(data)

            setattr(self, attr, v)
        except (ValueError, TypeError):
            pass

    def _assemble(self, action, parameter, data=None):
        if action == "read":
            # read parameter
            action = 0
        else:
            # describe parameter
            action = 10

        if data is None:
            data = "=?"

        data_len = len(data)
        msg = "{:03n}{:02n}{:03}{:02n}{}".format(
            self.address, action, parameter, data_len, data
        )

        return "{}{:03n}".format(msg, calc_checksum(msg))

    def _get_data(self, resp):
        match = RESPONSE_RE.search(resp)
        if match:
            dl = match.group("datalength")
            pattern = make_pattern(dl)
            match = re.search(pattern, resp)
            self.debug("{} {}".format(match, pattern))
            if match:
                if check_checksum(resp, match.group("checksum")):
                    data = match.group("data")
                    return data

    def pump_view(self):
        v = View(
            BorderVGroup(
                HGroup(UItem(
                        "onoff_button", editor=ButtonEditor(label_value="onoff_label")
                    ),
                    UItem(
                        "standby_button", editor=ButtonEditor(label_value="onoff_label")
                    ),
                ),
                Item(
                    "set_speed",
                    label="SetSpeed hz (308)",
                    editor=LCDEditor(width=100, height=50),
                ),
                Item(
                    "actual_speed",
                    label="ActualSpeed hz (309)",
                    editor=LCDEditor(width=100, height=50),
                ),
                Item(
                    "drive_current",
                    label="DriveCurrent A (310) ",
                    editor=LCDEditor(width=100, height=50),
                ),
                label=self.name,
            )
        )
        return v


# ============= EOF =============================================
