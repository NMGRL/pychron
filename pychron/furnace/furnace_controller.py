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
from pychron.hardware.core.abstract_device import AbstractDevice


@provides(IFurnaceController)
class FurnaceController(AbstractDevice):
    def read_output_percent(self, **kw):
        if self._cdevice:
            return self._cdevice.read_output_percent(**kw)

    def get_water_flow_state(self, **kw):
        if self._cdevice:
            return self._cdevice.get_water_flow_state(**kw)

    def get_summary(self, **kw):
        if self._cdevice:
            return self._cdevice.get_summary(**kw)

    def set_setpoint(self, v, **kw):
        if self._cdevice:
            return self._cdevice.set_setpoint(v, **kw)

    def get_output(self):
        r = 0
        if self._cdevice:
            r = self._cdevice.get_output()
        return r or 0

    def get_setpoint(self, **kw):
        r = 0
        if self._cdevice:
            r = self._cdevice.get_setpoint()
        return r or 0

    def get_response(self, **kw):
        o = 0
        if self._cdevice:
            o = self._cdevice.get_process_value()

        return o or 0

    def test_connection(self):
        if self._cdevice:
            return self._cdevice.test_connection()
        else:
            return False

    def set_pid(self, pstr):
        if self._cdevice:
            return self._cdevice.set_pid(pstr)

# ============= EOF =============================================
