# ===============================================================================
# Copyright 2023 ross
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
from pychron.hardware.core.communicators.serial_communicator import SerialCommunicator
from pychron.hardware.core.core_device import CoreDevice

STX = "5B"
ACK = b"\xAA"
NAK = b"\x3F"


def is_ack(resp):
    return resp == ACK


class UC2000(CoreDevice):
    """

    :::
    website: https://novantaphotonics.com/wp-content/uploads/2021/12/NOVT_UC2000_Manual.pdf
    description: UC-2000 Universal Laser Controller

    """

    def _load_communicator(self, config, comtype, *args, **kw):
        self.communicator = SerialCommunicator(name="uc2000")
        self.communicator.load(config, self.config_path)
        self.communicator.baudrate = 9600
        return True

    def initialize(self, *args, **kw):
        return True

    def load_additional_args(self, config):
        return True

    def enable(self, *args, **kw):
        return self._enable_laser(**kw)

    def disable(self, *args, **kw):
        return self._disable_laser()

    def set_laser_power(self, percentage, *args, **kw):
        """ """
        if 0 <= percentage <= 100:
            cmd = "7F"
            databyte = f"{percentage * 2:x}"
            # checksum = self._calculate_checksum(cmd, databyte)
            # resp = self._ask(f"{cmd}{databyte}{checksum}")

            resp = self._ask(cmd, databyte)
            self.debug(f"set laser power {percentage} {resp}")

    def get_status(self):
        status = self.communicator.ask("7E")
        self.debug(f"status {status}")

    # private
    def _ask(self, cmd, databyte=None, default=None, nbytes=1):
        chksum = self._calculate_checksum(cmd, databyte)
        cmd = f"{STX}{cmd}"

        if databyte:
            cmd = f"{cmd}{databyte}"

        cmd = f"{cmd}{chksum}"
        self.debug(f"ask {cmd}")

        import codecs
        command = cmd
        command = bytes(command, "utf-8")
        command = codecs.decode(command, "hex")
        print(cmd, command)

        resp = self.communicator.ask(cmd, verbose=True, is_hex=True)
        if resp != ACK:
            self.warning(
                f"response was not an ACK. resp={resp}. returning default={default}"
            )
            resp = default

        return resp

    def _calculate_checksum(self, cmd, value=None):
        d = int(cmd, 16)
        if value is not None:
            d += int(value, 16)
        nc = d & 255
        ones_compliment = nc ^ 255
        return f"{ones_compliment:02x}"

    def _enable_laser(self, **kw):
        cmd = "75"
        return is_ack(self._ask(cmd))

    def _disable_laser(self):
        cmd = "76"
        return is_ack(self._ask(cmd))


if __name__ == '__main__':
    uc = UC2000()
    uc.set_laser_power(63)
# ============= EOF =============================================
