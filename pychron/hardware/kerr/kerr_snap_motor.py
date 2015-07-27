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
# =============standard library imports ========================
# =============local library imports  ==========================
from kerr_motor import KerrMotor
class KerrSnapMotor(KerrMotor):
    """
    Snap Motor

    """
    def _build_io(self):
        """
            picsrvsc.pdf p.35
            I/O Control
            18   04
            cmd  iobit

            Bit 0 - Not used (clear to 0 for future compatibility)
            Bit 1 - Not used (clear to 0 for future compatibility)
            Bit 2 - Enable limit switch protection, turn motor off when limit is hit
            Bit 3 - Enable limit switch protection, stop abruptly when limit is hit
            Bit 4 - Enable 3-Phase commutation output mode
            Bit 5 - Enable Antiphase PWM output mode
            Bit 6 - Set fast path option for path control mode
            Bit 7 - Enable Step & Direction input mode


            04=00000100
            08=00001000
            14(20)=00010100 enable 3 phase
            24(36)=00100100 enable antiphase
        """
        return '1808'

    def _build_gains(self):
        """
            F6  B004 2003 F401 E803 FF 00 E803 01 01 01
            cmd p    d    i    il   ol cl el   sr db sm

            B004 2003 F401 B004 FF 00 6400 010101

            0064 03e8 0000 0000 ff 00 0fa0 01 01 01
        """
        flip_nibbles = True

        p = (1900, 4, flip_nibbles)
        d = (1000, 4, flip_nibbles)
        i = (100, 4, flip_nibbles)
        il = (4000, 4, flip_nibbles)
        ol = (255, 2)
        cl = (0, 2)
        el = (4000, 4, flip_nibbles)
        sr = (1, 2)
        db = (1, 2)
        sm = (1, 2)
        gains = self._build_hexstr(p, d, i, il, ol, cl, el, sr, db, sm)
        return 'F6{}'.format(gains)


#        return ''.join(['F6'] + map(hexfmt, [p, d, i, il, ol, cl, el, sr, db, sm]))

#    def _initialize_(self, *args, **kw):
#        '''
#        '''
#
#        addr = self.address
#        commands = [(addr, '1706', 100, 'stop motor, turn off amp'),
#                 (addr, '1804', 100, 'configure io pins'),
#                 (addr, 'F6B0042003F401E803FF00E803010101', 100, 'set gains'),
#                 (addr, '1701', 100, 'turn on amp'),
#                 (addr, '00', 100, 'reset position')
#                 ]
#        self._execute_hex_commands(commands)
#
#        self._home_motor(*args, **kw)
