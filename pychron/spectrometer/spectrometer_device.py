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

# ============= enthought library imports =======================
from traits.api import Any, Property

# ============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable


# from traitsui.api import View, Item, Group, HGroup, VGroup
# ============= standard library imports ========================


class SpectrometerDevice(ConfigLoadable):
    microcontroller = Any
    spectrometer = Any
    simulation = Property

    def _get_simulation(self):
        s = True
        if self.microcontroller:
            s = self.microcontroller.simulation
        return s

    def finish_loading(self):
        pass

    def ask(self, cmd, *args, **kw):
        if self.microcontroller:
            resp = self.microcontroller.ask(cmd, *args, **kw)
            resp = self.handle_response(cmd, resp)
            return resp

    def read(self, *args, **kw):
        if self.microcontroller:
            return self.microcontroller.read(*args, **kw)

    def tell(self, *args, **kw):
        if self.microcontroller:
            self.microcontroller.tell(*args, **kw)
    # def handle_response(self, cmd, resp):
    #     return resp
# ============= EOF =============================================
