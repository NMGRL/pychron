# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.base_linear_drive import BaseLinearDrive
from pychron.hardware.core.core_device import CoreDevice
ERROR_MAP = {}

class MDriveMotor(CoreDevice, BaseLinearDrive):
	def load_additional_args(self, config):
        args = [
            ('Motion', 'steps', 'int'),
            ('Motion', 'min_steps', 'int'),
            ('Motion', 'sign'),
            ('Motion', 'velocity'),
            ('Motion', 'acceleration'),

            ('Homing', 'home_delay'),
            ('Homing', 'home_velocity'),
            ('Homing', 'home_acceleration'),
            ('Homing', 'home_at_startup', 'boolean'),
            ('Homing', 'home_position'),
            ('Homing', 'home_limit'),

            ('General', 'min'),
            ('General', 'max'),
            ('General', 'nominal_position'),
            ('General', 'units')]
        self._load_config_attributes(config, args)

        self.linear_mapper_factory()
        return True

    def is_simulation(self):
		return self.simulation

    def move_absolute(self, pos, block=True):
        self._move(pos, False, block)

    def move_relative(self, pos, block=True):
        self._move(pos, True, block)
        
     def set_initial_velocity(self, v):
        self._set_var('VI', v)
        
    def set_velocity(self, v):
        self.tell('VM {}'.format(v))

    def set_acceleration(self, a):
        self.tell('A {}'.format(a))

    def set_slew(self, v):
        self.tell('SL {}'.format(v))
    
    def set_encoder_position(self, v):
        self.tell('P {}'.format(v))
        
    # private
    def _set_var(self, var, val, check_error=True):
        ret = True
        self.tell('{} {}'.format(var, val))
        if self.check_error:
            eflag = self._get_var('EF')
            if eflag == 1:
                ecode=self._get_var('ER')
                estr=ERROR_MAP.get(ecode, 'See MCode Programming Manual')
                self.warning('Error setting {}={} ErrorCode={}. Error={}'.format(var,val,ecode,estr))
                ret = False
        return ret
        
    def _get_var(self, c, as_int=True):
        resp = self.ask('PR {}'.format(c))
        self.info('Variable {}={}'.format(c,resp)
        if as_int:
            resp = int(resp)
        return resp
            
    def _move(self, pos, relative, block):
        cmd = 'MR' if relative else 'MA'
        self.tell('{} {}'.format(cmd, pos))
        if block:
            self._block()
            self.info('move complete')
            
    def _moving(self):
        """
        0= Not Moving
        1= Moviing
        """
        resp = self._get_var('M')
        return resp==1
    
    def _block(self):
        while 1:
            if not self._moving():
                break
            
            time.sleep(0.1)
    
    def _read_motor_position(self, *args, **kw):
        pos = self._get_var('P')
        return pos

if __name__ == '__main__':
    from pychron.paths import paths

    paths.build('_dev')
    m = MDriveMotor(name='mdrive')
    m.bootstrap()

# ============= EOF =============================================



