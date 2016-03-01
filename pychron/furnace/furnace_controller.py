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
from traits.api import Interface, provides
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.furnace.ifurnace_controller import IFurnaceController
from pychron.hardware.core.abstract_device import AbstractDevice


@provides(IFurnaceController)
class FurnaceController(AbstractDevice):
    def read_setpoint(self, **kw):
        if self._cdevice:
            return self._cdevice.read_setpoint(**kw)

    def set_setpoint(self, v, **kw):
        if self._cdevice:
            return self._cdevice.set_setpoint(v, **kw)
# ============= EOF =============================================
