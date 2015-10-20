# ===============================================================================
# Copyright 2011 Jake Ross
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



# =============enthought library imports=======================
from traits.api import Any, Str

# =============standard library imports ========================
import ConfigParser
# =============local library imports  ==========================
from pychron.config_loadable import ConfigLoadable
import time
class KerrDevice(ConfigLoadable):
    '''
        Base class for Kerr devices
    '''
    parent = Any
    address = Str('01')

    def ask(self, cmd, **kw):
        '''         
        '''
        if self.parent:
            return self.parent.ask(cmd, **kw)

    def tell(self, cmd, **kw):
        '''
        '''
        if self.parent:
            self.parent.tell(cmd, **kw)

    def load(self, path):
        '''
        '''

        config = ConfigParser.ConfigParser()
        config.read(path)

        self.set_attribute(config, 'address', 'General', 'address')
        self.load_additional_args(config)

#    def load_additional_args(self, config):
#        pass

    def _execute_hex_commands(self, commands, delay=None, **kw):
        '''
        '''
        # commands list of tuples (addr,hex-command,delay,description)
        for cmd in commands:
            self._execute_hex_command(cmd, **kw)
            if delay:
                time.sleep(delay * 0.001)


    def _execute_hex_command(self, cmd, tell=False, nbytes=2, **kw):
        '''
        '''
        addr, cmd, delay, desc = cmd

        cmd = self._build_command(addr, cmd)
        r = None
        if cmd is not None:
            if desc:
                self.info(desc)
            func = self.ask if not tell else self.tell
            r = func(cmd, is_hex=True, delay=delay, nbytes=nbytes, **kw)
#            r = self.ask(cmd, is_hex=True, delay=delay, **kw)

        return r

    def _build_command(self, addr, cmd):
        '''
        '''
        cmd = '{}{}'.format(addr, cmd)

        if self._check_command_len(cmd):
            chsum = self._calc_checksum(cmd)
            return 'AA{}{}'.format(cmd, chsum)

    def _check_command_len(self, cmd):
        '''
            the high nibble of the command sequence indicates the number of
            data bits to follow
        
        '''
        high_nibble = int(cmd[2:3], 16)
        data_bits = cmd[4:]
        cb = high_nibble == len(data_bits) / 2
        if not cb:
            self.warning('{} != len({})/2, {}'.format(high_nibble, data_bits, len(data_bits) / 2))
        return cb

    def _calc_checksum(self, cmd):
        '''
        '''
        s = 0
        for i in range(0, len(cmd), 2):
            bit = cmd[i:i + 2]
            s += int(bit, 16)

        r = '%02X' % s
        return r[-2:]

    def _check_bits(self, bits):
        '''
        '''
        rbits = []
        if isinstance(bits, int):
            for i in range(16):
                if (bits >> i) & 1 == 1:
                    rbits.append(i)
        return rbits

    def _get_io_bits(self):
        return ['0',  # bit 4
                '1',
                '1',
                '1',
                '0']  # bit 0

    def _set_io_state(self, bit, state):
        iobits = self._get_io_bits()
        n = len(iobits) - 1
        iobits[n - bit] = str(int(state))
        iob = int('000' + ''.join(iobits), 2)
        cmd = '{}{:02X}'.format('18', iob)
        cmds = [(self.address, cmd, 100, 'set io {} {}'.format(bit, state))]
        self._execute_hex_commands(cmds)
# =========================EOF======================================
