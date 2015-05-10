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
from traits.has_traits import provides
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_list
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.ichiller import IChiller
from pychron.remote_hardware.registry import registered_function


@provides(IChiller)
class PychronChiller(CoreDevice):
    @registered_function(camel_case=True, returntype=to_list)
    def get_faults(self):
        pass

    @registered_function(camel_case=True, returntype=float)
    def get_coolant_out_temperature(self):
        pass

    def get_setpoint(self):
        pass

    def set_setpoint(self, v):
        pass

# ============= EOF =============================================



