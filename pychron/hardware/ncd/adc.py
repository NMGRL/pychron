"""
    National Control Devices
    
   http://www.controlanything.com/ 
   
   The Complete ProXR Command Set:
   http://www.controlanything.com/Relay/Device/A0010
   http://assets.controlanything.com/manuals/ProXR.pdf
"""

# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
# ============= enthought library imports =======================
# ============= standard library imports ========================
import math
import struct

# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_csv_str
from pychron.hardware.ncd.ncd_device import NCDDevice


class ProXRADCExpansion(NCDDevice):
    def read_channel(self, channel, nbits=8):
        if nbits == 10:
            start = 157
            nbytes = 2
        else:
            start = 149
            nbytes = 1
        idx = int(channel) + start
        cmdstr = self._make_cmdstr(254, idx)
        resp = self.ask(cmdstr, nbytes=nbytes)
        return int(resp, 16)


EIGHT_BIT_SINGLE = [195, 203, 208]
TWELVE_BIT_SINGLE = [199, 207, 209]

EIGHT_BIT_BANKS = [192, 193, 194]
TWELVE_BIT_BANKS = [196, 197, 198]


class ProXRADC(NCDDevice):
    max_voltage = 5

    def read_device_info(self):
        cmdstr = self._make_cmdstr(254, 246)
        resp = self.ask(cmdstr, nchars=5, remove_eol=False)
        return resp

    def read_bank(self, bank=0, nbits=8, verbose=True):
        """
        return voltages (V) measured on channels in "bank"
        nbits= 8 or 12 resolution of measurement
        """
        self._check_nbits(nbits)

        if nbits == 8:
            nbytes = 16
            bank_idxs = EIGHT_BIT_BANKS
        else:
            nbytes = 32
            bank_idxs = TWELVE_BIT_BANKS

        idx = bank_idxs[bank]
        cmdstr = self._make_cmdstr(254, idx)
        resp = self.ask(cmdstr, nchars=nbytes, verbose=verbose, remove_eol=False)
        vs = self._map_to_voltage(resp, nbits, nbytes)
        if verbose:
            self.debug("bank={} nbits={} values={}".format(bank, nbits, to_csv_str(vs)))
        return vs

    def read_channel(self, channel, nbits=8, verbose=True):
        """
        return voltage (V) measured on "channel"
        nbits= 8 or 12. resolution of measurement
        """
        self._check_nbits(nbits)

        channel = int(channel)
        if nbits == 12:
            bank = TWELVE_BIT_SINGLE
            nbytes = 2
        else:
            bank = EIGHT_BIT_SINGLE
            nbytes = 1

        bank_idx = bank[channel // 16]
        channel_idx = channel % 16

        cmdstr = self._make_cmdstr(254, bank_idx, channel_idx)
        resp = self.ask(cmdstr, nchars=nbytes, verbose=verbose, remove_eol=False)
        if resp:
            volts = self._map_to_voltage(resp, nbits, nbytes)[0]
        else:
            volts = self.get_random_value()

        if verbose:
            self.debug("bank={} nbits={} volts={}".format(bank_idx, nbits, volts))
        return volts

    def _parse_response(self, v):
        if not v:
            v = self.get_random_value()
        return v

    def _check_nbits(self, nbits):
        if not nbits in (8, 12):
            raise Exception("Invalid nbits {}. use 8 or 12")

    def _map_to_voltage(self, resp, nbits, nbytes):
        if resp is None:
            return (0,)

        f, s = ">B", 1
        if nbits == 12:
            f, s = "<h", 2

        m = 2**nbits - 1

        def vfunc(v):
            nd = int(math.log10(m))
            return round(v / float(m) * self.max_voltage, nd)

        return [
            vfunc(struct.unpack(f, resp[i : i + s])[0]) for i in range(0, nbytes, s)
        ]


if __name__ == "__main__":
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import paths

    paths.build("_dev")

    logging_setup("adc", use_archiver=False)

    # paths.build('_dev')
    # [254][199][0]
    a = ProXRADC(name="ProXRADC")
    # a = MultiBankADCExpansion(name='proxr_adc')
    # a.bootstrap()
    a.load_communicator("serial", port="usbserial-A5018URQ", baudrate=115200)
    a.initialize()
    a.open()
    # print 'read bank', a.read_bank()
    # a.read_bank(nbits=12)
    # a.read_bank(1, nbits=12)
    # a.read_bank(2, nbits=12)

    import time

    for i in range(100):
        # for j in range(8):
        #     a.read_channel(j, nbits=8)
        # time.sleep(0.5)
        a.read_bank(0, nbits=12)
        a.read_bank(1, nbits=12)
        a.read_bank(2, nbits=12)
        a.read_channel(0, nbits=12)
        a.read_channel(0, nbits=8)
        a.read_channel(2, nbits=12)
        a.read_channel(2, nbits=8)
        time.sleep(0.5)
        # a.read_bank()

        # print a._communicator.handle
        # a.read_device_info()
        # print 'read channel 0',a.read_channel(0, nbits=8)
        # print 'read channel 0 12bit',a.read_channel(0, nbits=12)
# ============= EOF =============================================
