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
from fusions_logic_board import FusionsLogicBoard

class FusionsDiodeLogicBoard(FusionsLogicBoard):
    '''
    '''
    def _set_laser_power(self, p, m):
        '''
        '''
        self.parent.set_laser_power(p, m)

    def set_enable_onoff(self, onoff):
        '''
        '''
#        if onoff:
#            cmd = self.prefix + 'DRV0 1'
#        else:
#            cmd = self.prefix + 'DRV0 0'

        cmd = self._build_command('DRV0', '1' if onoff else '0')
        self.ask(cmd)

    def set_interlock_onoff(self, onoff):
        '''
        '''
#        if onoff:
#            cmd = self.prefix + 'IOWR1 1'
#        else:
#            cmd = self.prefix + 'IOWR1 0'
        cmd = self._build_command('IOWR1', '1' if onoff else '0')
        self.ask(cmd)

#    def _beam_motor_default(self):
#        '''
#        '''
#        return KerrThorMotor(name='beam', parent=self)
# ====================== EOF ===========================================
