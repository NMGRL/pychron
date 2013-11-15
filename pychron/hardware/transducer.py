#===============================================================================
# Copyright 2013 Jake Ross
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
from numpy import poly1d
from traits.api import Float, Str
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.hardware.adc.adc_device import ADCDevice


class Transducer(ADCDevice):
    """
        abstract device the reads an input voltage and maps to an output value
    """
    scan_func = 'read_voltage'
    mapped_name = Str

    def load_additional_args(self, config):
        """
            load mapping

            poly1d([3,2,1]) == 3*x^2+2*x+1

        """
        coeffs = self.config_get(config, 'Mapping', 'coefficients', default=[1, 0])
        try:
            coeffs = eval(coeffs)
            self._mapping_poly = poly1d(coeffs)
        except Exception:
            self.warning('Invalid mapping coefficients: {}'.format(coeffs))

        self.set_attribute(config, 'mapped_name', 'Mapping', 'name')
        if self.mapped_name:
            self.add_trait(self.mapped_name, Float)
            u = self.config_get(config, 'Mapping', 'units', default='')
            self.graph_ytitle = '{} ({})'.format(self.mapped_name.capitalize(), u)

        return super(Transducer, self).load_additional_args(config)


    def read_voltage(self, **kw):
        ret = super(Transducer, self).read_voltage(**kw)
        return self.map_data(ret)

    def get(self, **kw):
        if self._scanning:
            v = self.current_scan_value
        else:
            v = self.read_voltage(**kw)

        ret = self.map_data(v)
        return ret

    def map_data(self, v):
        """
            map a voltage to data space
        """
        v = self._mapping_poly(v)
        setattr(self, self.mapped_name, v)
        return v

#============= EOF =============================================
