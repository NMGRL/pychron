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
    '''
    Snap Motor 
    
    '''
    def _build_io(self):
        '''
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
        '''
        return '1804'


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
