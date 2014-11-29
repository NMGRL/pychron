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
from pychron.hardware.core.data_helper import make_bitarray
'''
    National Control Devices
    
   http://www.controlanything.com/ 
   
   The Complete ProXR Command Set:
   http://www.controlanything.com/Relay/Device/A0010
   http://assets.controlanything.com/manuals/ProXR.pdf
'''


from pychron.paths import paths
from pychron.core.helpers.logger_setup import logging_setup
logging_setup('prox')
paths.build('_prox')

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.ncd import ON_MAP, OFF_MAP, STATE_MAP
from pychron.hardware.ncd.ncd_device import NCDDevice


class ProXR(NCDDevice):
    '''
        implement the actuator interface
        open_channel
        close_channel
        get_channel_state
    '''
    def open_channel(self, channel, *args, **kw):
        '''
            idx=1-255
            32 banks of 8
            
            bank = idx/8
            
        '''
        name = self._set_bank(channel)
        if name:
            local_idx = ON_MAP[name]
#            print local_idx
#            cmdstr = self._make_cmdstr(254, local_idx)
#            resp = self.ask(cmdstr, nchars=1)
#            return resp == 'U'  # hex(85)
            return self._ask_ok(254, local_idx)

    def close_channel(self, channel, *args, **kw):
        name = self._set_bank(channel)
        if name:
            local_idx = OFF_MAP[name]
#            cmdstr = self._make_cmdstr(254, local_idx)
            return self._ask_ok(254, local_idx)
#            resp = self.ask(cmdstr, nchars=1)
#            return resp == 'U'  # hex(85)

    def get_contact_state(self, channel, bank=None, *args, **w):
        if bank is None:
            idx, bank = self._get_bank_idx(channel)
        else:
            idx = self._get_channel_idx(channel)

        cmdstr = self._make_cmdstr(254, 175, bank - 1)
        resp = self.ask(cmdstr, nchars=1)
        a = ord(resp)

        ba = make_bitarray(a)
        return bool(int(ba[8 - idx]))
#        print resp, ord(resp)

    def get_channel_state(self, channel, *args, **kw):
        name = self._set_bank(channel)
        if name:
            local_idx = STATE_MAP[name]
            cmdstr = self._make_cmdstr(254, local_idx)
            resp = self.ask(cmdstr, nchars=1)  # returns 1 or 0
            return bool(int(resp))

    def get_channel_states(self, *args, **kw):
        cmdstr = self._make_cmdstr(254, 24)
        resp = self.ask(cmdstr)

    def _ask_ok(self, *args):
        cmdstr = self._make_cmdstr(*args)
        return self.ask(cmdstr, nchars=1) == 'U'


# =====================================    ==========================================
# configuration
# ===============================================================================


# ===============================================================================
# private
# ===============================================================================
    def _set_bank(self, channel):
        idx, bank = self._get_bank_idx(channel)
#        cmdstr = self._make_cmdstr(254, 49, bank)
        if self._ask_ok(254, 49, bank):  # ord('U')== decimal 85, hex 55
            return str(idx % 8)
    def _get_channel_idx(self, channel):
        if isinstance(channel, str):
            idx = int(channel)
        elif isinstance(channel, int):
            idx = channel
        else:
            idx = channel.name
        return idx

    def _get_bank_idx(self, channel):
        idx = self._get_bank_idx(channel)
        bank = idx / 8 + 1
        return idx, bank


if __name__ == '__main__':
    a = ProXR(name='proxr_actuator')
    a.bootstrap()
#    a.open_channel(3)
#    time.sleep(1)
#    a.close_channel(3)
#    time.sleep(1)
    print a.get_contact_state(6, bank=11)


# ============= EOF =============================================
