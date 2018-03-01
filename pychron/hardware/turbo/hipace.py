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

from __future__ import absolute_import
from pychron.hardware.core.communicators.serial_communicator import SerialCommunicator
from pychron.hardware.core.core_device import CoreDevice
import re

BASE = r'^(?P<address>\d{3})(?P<action>\d{2})(?P<parameter>\d{2})(?P<datalength>\d{2})'
RESPONSE_RE = re.compile(BASE)


def make_pattern(dl):
    return '{}(?P<data>\d{{{}}})(?P<checksum>\d{3}'.format(BASE, dl)


def check_checksum(resp, chksum):
    r = resp[:-3]
    return calc_checksum(r) == int(chksum)


def calc_checksum(msg):
    checksum = sum((ord(mi) for mi in msg))
    return checksum % 256


class HiPace(CoreDevice):

    def read_set_speed(self):
        return self._read_parameter(308)

    def read_actual_speed(self):
        return self._read_parameter(309)

    def _read_parameter(self, param):
        resp = self.ask('read', param)
        data = self._get_data(resp)
        try:
            return int(data)
        except (ValueError, TypeError):
            pass

    def _get_data(self, resp):
        match = RESPONSE_RE.search(resp)
        if match:
            dl = match.group('datalength')
            pattern = make_pattern(dl)
            match = re.search(pattern, resp)
            if match:
                if check_checksum(resp, match.group('checksum')):
                    data = match.group('data')
                    return data


class HiPaceCommunicator(SerialCommunicator):

    def ask(self, action, parameter, data=None, *args, **kw):
        cmd = self._assemble(action, parameter, data)
        return super(HiPaceCommunicator, self).ask(cmd, *args, **kw)

    def _assemble(self, action, parameter, data):
        if action == 'read':
            # read parameter
            action = 0
        else:
            # describe parameter
            action = 10

        if data is None:
            data = '=?'

        data_len = len(data)
        msg = '{:03n}{:02n}{:03}{:02n}{}'.format(self.address, action, parameter, data_len, data)

        return '{}{:03n}'.format(msg, self._calc_checksum(msg))

# ============= EOF =============================================
