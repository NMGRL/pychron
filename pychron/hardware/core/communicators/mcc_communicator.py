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
from mcculw.enums import ULRange

from pychron.hardware.core.communicators.communicator import Communicator


class MccCommunicator(Communicator):
    """
    https://github.com/mccdaq/mcculw
    """
    board_num = 0

    def load(self, config, path):
        self.board_num = self.config_get(config, 'Communications', 'board_num')
        return super(ModbustcpCommunicator, self).load(config, path)

    def open(self, *args, **kw):
        return True

    def initialize(self, *args, **kw):
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
        bit_num = self._get_bit_num(channel)

        self.debug('channel={}, bit_num={}, bit_value={}'.format(channel, bit_num, bit_value))

        # Output the value to the bit
        ul.d_bit_out(board_num, port.type, bit_num, bit_value)

    def d_in(self, channel):
        port = self._get_port(channel)
        bit_num = self._get_bit_num(channel)

        bit_value = ul.d_bit_in(board_num, port.type, bit_num)
        return bit_value

    def _get_bit_num(self, channel):
        channel = str(channel)
        bit_num = int(channel[1:])
        self.debug('channel={}  bit_num={}', channel, bit_num)
        return bit_num

    def _get_port(self, channel):
        port_id = int(channel[0])
        self.debug('channel={} port={}'.format(port_id))

        daq_dev_info = DaqDeviceInfo(self.board_num)
        if not daq_dev_info.supports_digital_io:
            raise Exception('Error: The DAQ device does not support '
                            'digital I/O')

        self.debug('Active DAQ device: {} {}', daq_dev_info.product_name, daq_dev_info.unique_id)

        dio_info = daq_dev_info.get_dio_info()
        try:
            port = dio_info[port_id]
            return port
        except IndexError:
            self.debug('Invalid port_id={}', port_id)

        # Find the first port that supports input, defaulting to None
        # if one is not found.
        # port = next((port for port in dio_info.port_info if port.supports_input),
        #             None)
        # if not port:
        #     raise Exception('Error: The DAQ device does not support '
        #                     'digital input')


# ============= EOF =============================================
