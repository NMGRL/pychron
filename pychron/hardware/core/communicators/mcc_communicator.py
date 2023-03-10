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
from mcculw import ul
from mcculw.enums import ULRange, InterfaceType, DigitalIODirection, DigitalPortType
from mcculw.device_info import DaqDeviceInfo

from pychron.hardware.core.communicators.communicator import Communicator


def config_first_detected_device(board_num, dev_id_list=None):
    """Adds the first available device to the UL.  If a types_list is specified,
    the first available device in the types list will be add to the UL.
    Parameters
    ----------
    board_num : int
        The board number to assign to the board when configuring the device.
    dev_id_list : list[int], optional
        A list of product IDs used to filter the results. Default is None.
        See UL documentation for device IDs.
    """
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    if not devices:
        raise Exception("Error: No DAQ devices found")

    print("Found", len(devices), "DAQ device(s):")
    for device in devices:
        print(
            "  ",
            device.product_name,
            " (",
            device.unique_id,
            ") - ",
            "Device ID = ",
            device.product_id,
            sep="",
        )

    device = devices[0]
    if dev_id_list:
        device = next(
            (device for device in devices if device.product_id in dev_id_list), None
        )
        if not device:
            err_str = "Error: No DAQ device found in device ID list: "
            err_str += ",".join(str(dev_id) for dev_id in dev_id_list)
            raise Exception(err_str)

    # Add the first DAQ device to the UL with the specified board number
    ul.create_daq_device(board_num, device)


PORT_MAP = {
    0: 10,
    1: 10,
    2: 10,
    3: 10,
    4: 10,
    5: 10,
    6: 10,
    7: 10,
    8: 11,
    9: 11,
    10: 11,
    11: 11,
    12: 11,
    13: 11,
    14: 11,
    15: 11,
    16: 12,
    17: 12,
    18: 12,
    19: 12,
    20: 13,
    21: 13,
    22: 13,
    23: 13,
    24: 14,
    25: 14,
    26: 14,
    27: 14,
    28: 14,
    29: 14,
    30: 14,
    31: 14,
    32: 15,
    33: 15,
    34: 15,
    35: 15,
    36: 15,
    37: 15,
    38: 15,
    39: 15,
    40: 16,
    41: 16,
    42: 16,
    43: 16,
    44: 17,
    45: 17,
    46: 17,
    47: 17,
    48: 18,
    49: 18,
    50: 18,
    51: 18,
    52: 18,
    53: 18,
    54: 18,
    55: 18,
    56: 19,
    57: 19,
    58: 19,
    59: 19,
    60: 19,
    61: 19,
    62: 19,
    63: 19,
    64: 20,
    65: 20,
    66: 20,
    67: 20,
    68: 21,
    69: 21,
    70: 21,
    71: 21,
    72: 22,
    73: 22,
    74: 22,
    75: 22,
    76: 22,
    77: 22,
    78: 22,
    79: 22,
    80: 23,
    81: 23,
    82: 23,
    83: 23,
    84: 23,
    85: 23,
    86: 23,
    87: 23,
    88: 24,
    89: 24,
    90: 24,
    91: 24,
    92: 25,
    93: 25,
    94: 25,
    95: 25,
}


class MccCommunicator(Communicator):
    """
    https://github.com/mccdaq/mcculw
    """

    board_num = 0
    config_on_startup = True

    def load(self, config, path):
        self.board_num = self.config_get(
            config, "Communications", "board_num", cast="int"
        )
        # self.config_on_startup = self.config_get(config, 'General',  'config_on_startup', cast='boolean')

        return super(MccCommunicator, self).load(config, path)

    def open(self, *args, **kw):
        return True

    def initialize(self, *args, **kw):
        config_first_detected_device(self.board_num)
        self.port_bits = {}
        if self.config_on_startup:
            port = self._get_port("10-0")
            ul.d_config_port(self.board_num, port.type, DigitalIODirection.OUT)
            port = self._get_port("11-0")
            ul.d_config_port(self.board_num, port.type, DigitalIODirection.OUT)

        return True

    def a_in(self, channel, ai_range=None):
        if ai_range is None:
            ai_range = ULRange.BIP5VOLTS

        value = ul.a_in(self.board_num, channel, ai_range)
        # Convert the raw value to engineering units
        eng_units_value = ul.to_eng_units(board_num, ai_range, value)
        return eng_units_value

    def d_out(self, channel, bit_value):
        channel = str(channel)
        port = self._get_port(channel)
        if port:
            bit_num = self._get_bit_num(channel)

            self.debug(
                "channel={}, bit_num={}, bit_value={}".format(
                    channel, bit_num, bit_value
                )
            )
            # if port.is_port_configurable:
            #    self.debug('configuring {} to OUT'.format(port.type))
            #    ul.d_config_port(self.board_num, port.type, DigitalIODirection.OUT)
            # Output the value to the bit

            try:
                ul.d_bit_out(self.board_num, port.type, bit_num, bit_value)
            except BaseException:
                self.debug_exception()

    def d_in(self, channel):
        port = self._get_port(channel)
        if port:
            bit_num = self._get_bit_num(channel)

            bit_value = ul.d_bit_in(self.board_num, port.type, bit_num)
            return bool(bit_value)

    def _get_bit_num(self, channel):
        channel = str(channel)
        bit_num = int(channel.split("-")[1])
        self.debug("channel={}  bit_num={}".format(channel, bit_num))
        return bit_num

    def _get_port(self, channel):
        port_id = int(str(channel).split("-")[0])
        self.debug("channel={} port={}".format(channel, port_id))

        daq_dev_info = DaqDeviceInfo(self.board_num)
        if not daq_dev_info.supports_digital_io:
            raise Exception("Error: The DAQ device does not support " "digital I/O")

        self.debug(
            "Active DAQ device: {} {}".format(
                daq_dev_info.product_name, daq_dev_info.unique_id
            )
        )

        dio_info = daq_dev_info.get_dio_info()

        for i, p in enumerate(dio_info.port_info):
            self.debug(
                "{} {} {} {} {}".format(i, p, p.type, p.num_bits, p.supports_output)
            )

        for p in dio_info.port_info:
            if int(p.type) == port_id:
                return p
        else:
            self.debug("Invalid port_id={}", port_id)

        # Find the first port that supports input, defaulting to None
        # if one is not found.
        # port = next((port for port in dio_info.port_info if port.supports_input),
        #             None)
        # if not port:
        #     raise Exception('Error: The DAQ device does not support '
        #                     'digital input')


# ============= EOF =============================================
