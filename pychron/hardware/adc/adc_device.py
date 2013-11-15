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

#=============enthought library imports=======================
#=============standard library imports ========================

#=============local library imports  ==========================
from pychron.hardware.core.abstract_device import AbstractDevice

class ADCDevice(AbstractDevice):
#    scan_func = 'read_voltage'
    _rvoltage = 0
    channel = None

    def load_additional_args(self, config):
        if config.has_section('ADC'):
            klass = self.config_get(config, 'ADC', 'klass')
            pkgs = ('pychron.hardware.adc.analog_digital_converter',
                      'pychron.hardware.agilent.agilent_multiplexer',
                      'pychron.hardware.remote.agilent_multiplexer',
                      'pychron.hardware.ncd.adc'
            )

            for pi in pkgs:
                factory = self.get_factory(pi, klass)
                if factory:
                    break

            self.set_attribute(config, 'channel', 'ADC', 'channel')

#        adc = self.config_get(config, 'General', 'adc')
#
#        if adc is not None:

            self._cdevice = factory(name=klass,
                                    configuration_dir_name=self.configuration_dir_name
                                    )

            return True

    def read_voltage(self, **kw):
        '''
        '''
        if self._cdevice is not None:
            if self.channel:
                v = self._cdevice.read_channel(self.channel)
            else:
                v = self._cdevice.read_device(**kw)
            self._rvoltage = v
            return v


#============= EOF =====================================
