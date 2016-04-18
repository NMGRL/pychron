# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import provides, Int
# ============= standard library imports ========================
import json
import re
# ============= local library imports  ==========================
from pychron.furnace.furnace_controller import IFurnaceController
from pychron.core.communication_helper import trim_bool
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice

VER_REGEX = re.compile(r'\d+.\d+(.\d+){0,1}')


@provides(IFurnaceController)
class NMGRLFurnaceEurotherm(CoreDevice):
    water_flow_channel = Int

    def load_additional_args(self, config):
        self.set_attribute(config, 'water_flow_channel', 'DIO', 'water_flow_channel', cast='int')
        return super(NMGRLFurnaceEurotherm, self).load_additional_args(config)

    def test_connection(self):
        d = json.dumps({'command': 'GetVersion'})
        resp = self.ask(d)
        if resp:
            return VER_REGEX.match(resp) is not None
        else:
            return False

    @get_float(default=0)
    def read_output_percent(self, **kw):
        d = json.dumps({'command': 'GetPercentOutput'})
        return self.ask(d, **kw)

    @trim_bool
    def get_water_flow_state(self, **kw):
        d = json.dumps({'command': 'GetDIState', 'channel': self.water_flow_channel})
        return self.ask(d, **kw)

    def set_pid(self, pstr):
        d = json.dumps({'command': 'SetPID', 'pid': pstr})
        return self.ask(d)

    def set_setpoint(self, v, **kw):
        d = json.dumps({'command': 'SetSetpoint', 'setpoint': v})
        self.ask(d)

    @get_float(default=0)
    def get_setpoint(self, **kw):
        return self.ask('GetSetpoint')

    read_setpoint = get_setpoint

    def get_temperature(self, **kw):
        resp = self.ask('GetTemperature', **kw)
        try:
            return float(resp)
        except (TypeError, ValueError):
            pass

    read_temperature = get_temperature

    def get_process_value(self, **kw):
        resp = self.ask('GetProcessValue', **kw)
        try:
            return float(resp)
        except (TypeError, ValueError):
            pass

    def get_output(self):
        resp = self.ask('GetPercentOutput')
        try:
            return float(resp)
        except (TypeError, ValueError):
            pass

# ============= EOF =============================================
