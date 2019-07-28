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
from traits.api import provides
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.furnace.ifurnace_controller import IFurnaceController
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice


@provides(IFurnaceController)
class ThermoFurnaceController(CoreDevice):
    @get_float(default=0)
    def read_output_percent(self, **kw):
        cmd = 'GetPercentOutput'
        return self.ask(cmd)

    def get_summary(self, **kw):
        return 'No Summary'

    def set_setpoint(self, v, **kw):
        cmd = 'SetFurnaceStep {}'.format(v)
        self.ask(cmd)

    @get_float(default=0)
    def get_output(self, **kw):
        cmd = 'GetFurnaceOutput'
        return self.ask(cmd)

    @get_float(default=0)
    def get_setpoint(self, **kw):
        cmd = 'GetFurnaceSetpoint'
        return self.ask(cmd)

    @get_float(default=0)
    def get_response(self, **kw):
        cmd = 'GetFurnaceResponse'
        return self.ask(cmd)

    get_temperature = get_response
    get_process_value = get_response

    def test_connection(self):
        return True, ''

    def set_pid(self, pstr):
        cmd = ''
        self.ask(cmd)
# ============= EOF =============================================
