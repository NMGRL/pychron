# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Button, CStr
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.abstract_device import AddressableAbstractDevice
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.polyinomial_mapper import PolynomialMapper
from pychron.remote_hardware.registry import register, RHMixin, registered_function


class Pneumatics(AddressableAbstractDevice, RHMixin):
    scan_func = 'get_pressure'
    poly_mapper = None

    def load_additional_args(self, config):
        conv = 'Conversion'
        if config.has_section(conv):
            self.poly_mapper = PolynomialMapper()
            pmapper = self.poly_mapper
            coeffs = self.config_get(config, conv, 'coefficients')
            pmapper.parse_coefficient_string(coeffs)
            pmapper.output_low = self.config_get(config, conv, 'output_low', cast='float')
            pmapper.output_high = self.config_get(config, conv, 'output_high', cast='float')
            self.set_attribute(config, 'mapped_name', conv, 'name')

            if self.mapped_name:
                u = self.config_get(config, conv, 'units', default='')
                self.graph_ytitle = '{} ({})'.format(self.mapped_name.capitalize(), u)
        return super(Pneumatics, self).load_additional_args(config)

    @register('GetPneumatics')
    def get_pressure(self, **kw):
        v = self.get(**kw)
        if v is not None:
            if self.poly_mapper:
                v = self.poly_mapper.map_measured(v)
        return v


class PychronPneumatics(CoreDevice):
    @registered_function('GetPneumatics', camel_case=True, returntype=float)
    def get_pressure(self):
        pass

    def get(self, *args, **kw):
        return self.ask('Read {}'.format(self.name))

# ============= EOF =============================================



