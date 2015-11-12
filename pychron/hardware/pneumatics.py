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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.adc.adc_device import PolynomialMapperMixin
from pychron.hardware.core.abstract_device import AddressableAbstractDevice
from pychron.hardware.core.core_device import CoreDevice
# from pychron.remote_hardware.registry import register, registered_function
from pychron.tx.registry import tx_register_functions, register, registered_function


class Pneumatics(AddressableAbstractDevice, PolynomialMapperMixin):
    scan_func = 'get_pressure'

    def __init__(self, *args, **kw):
        super(Pneumatics, self).__init__(*args, **kw)
        tx_register_functions(self)

        # self.register_functions()

    def load_additional_args(self, config):
        self.load_mapping(config)
        return super(Pneumatics, self).load_additional_args(config)

    @register('GetPneumaticsPressure')
    def get_pressure(self, **kw):
        v = self.get(**kw)
        if v is not None:
            if self.poly_mapper:
                v = self.poly_mapper.map_measured(v)
        return v


class PychronPneumatics(CoreDevice):
    @registered_function('GetPneumaticsPressure', camel_case=True, returntype=float)
    def get_pressure(self):
        pass

    def get(self, *args, **kw):
        return self.ask('Read {}'.format(self.name))

# ============= EOF =============================================



