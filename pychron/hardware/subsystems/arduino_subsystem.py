#===============================================================================
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
#===============================================================================



#============= enthought library imports =======================
# from traitsui.api import View,Item,Group,HGroup,VGroup

#============= standard library imports ========================

#============= local library imports  ==========================

from pychron.hardware.arduino.arduino_gp_actuator import ArduinoGPActuator
from pychron.hardware.arduino.arduino_valve_actuator import ArduinoValveActuator
from pychron.hardware.arduino.arduino_fiber_light_module import ArduinoFiberLightModule
from subsystem import Subsystem

class ArduinoSubsystem(Subsystem):
    def load_additional_args(self, config):
        '''

        '''



        modules = self.config_get(config, 'General', 'modules')

        if modules is not None:
            for m in modules.split(','):
                _class_ = 'Arduino{}'.format(m)
                gdict = globals()
                if _class_ in gdict:
                    module = gdict[_class_](name=_class_,
                                            configuration_dir_name=self.configuration_dir_name
                                    )
                    module.load()
                    module._communicator = self._communicator
                    self.modules[m] = module
        return True

#============= EOF ====================================
