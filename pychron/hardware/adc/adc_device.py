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
from traits.api import Str
# =============standard library imports ========================
# =============local library imports  ==========================
from pychron.core import Q_

from pychron.hardware.core.abstract_device import AbstractDevice
from pychron.hardware.polyinomial_mapper import PolynomialMapper


class ADCDevice(AbstractDevice):
    _rvoltage = None
    channel = None
    scan_func = 'read_voltage'
    mapped_name = Str
    graph_ytitle = Str
    poly_mapper = None

    def __init__(self, *args, **kw):
        """
            polynomial mappers coefficients should be in the following form

            output=a*voltage+b

        """
        super(ADCDevice, self).__init__(*args, **kw)
        self.poly_mapper = PolynomialMapper()

    def load_additional_args(self, config):
        adc = 'ADC'
        if config.has_section(adc):
            klass = self.config_get(config, adc, 'klass')
            name = self.config_get(config, adc, default=klass)

            pkgs = ('pychron.hardware.adc.analog_digital_converter',
                    'pychron.hardware.agilent.agilent_multiplexer',
                    'pychron.hardware.remote.agilent_multiplexer',
                    'pychron.hardware.ncd.adc')

            for pi in pkgs:
                factory = self.get_factory(pi, klass)
                if factory:
                    break

            self.set_attribute(config, 'channel', adc, 'channel')
            self._cdevice = factory(name=name,
                                    configuration_dir_name=self.configuration_dir_name)

            conv = 'Conversion'
            if config.has_section(conv):
                pmapper = self.poly_mapper
                coeffs = self.config_get(config, conv, 'coefficients')
                pmapper.parse_coefficient_string(coeffs)
                pmapper.output_low = self.config_get(config, conv, 'output_low')
                pmapper.output_high = self.config_get(config, conv, 'output_low')
                self.set_attribute(config, 'mapped_name', conv, 'name')

                if self.mapped_name:
                    u = self.config_get(config, conv, 'units', default='')
                    self.graph_ytitle = '{} ({})'.format(self.mapped_name.capitalize(), u)

            return True

    def read_voltage(self, **kw):
        """
            red the voltage from the actual device
        """
        if self._cdevice is not None:
            if self.channel:
                v = self._cdevice.read_channel(self.channel)
            else:
                v = self._cdevice.read_device(**kw)

            if not isinstance(v, Q_):
                v = Q_(v, 'V')
            else:
                v = v.to('V')

            self._rvoltage = v
            return v

    def get(self, **kw):
        return self.get_output(**kw)

    def get_output(self, force=False):
        """
            get a mapped output value e.g Temperature

            if force is True, force a query to the device, otherwise
            use the stored value
        """
        if force or self._rvoltage is None:
            v = self.read_voltage()
        else:
            v = self._rvoltage

        return self.poly_mapper.map_measured(v)


# ============= EOF =====================================
