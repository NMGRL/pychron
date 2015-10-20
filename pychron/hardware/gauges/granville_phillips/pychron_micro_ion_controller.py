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
import time
from pychron.hardware.gauges.granville_phillips.micro_ion_controller import MicroIonController


class PychronMicroIonController(MicroIonController):

    def get_pressure(self, name, **kw):
        return self.ask('Get Pressure {} {}'.format(self.name, name), **kw)

    def get_ion_pressure(self, **kw):
        return self.ask('Get Pressure {} IG'.format(self.name))

    def get_convectron_a_pressure(self, **kw):
        return self.ask('GetPressure {} CG1'.format(self.name))

    def get_convectron_b_pressure(self, **kw):
        return self.ask('GetPressure {} CG2'.format(self.name))


class QtegraMicroIonController(MicroIonController):
    def get_pressures(self, verbose=False):
        kw = {'verbose': verbose, 'force': True}
        for d in self.gauges:
            ig = self.ask('GetParameter {}'.format(d.name), **kw)
            self._set_gauge_pressure(d.name, ig)

    # def get_pressure(self, name, **kw):
    #     k=''
    #     return self.ask('GetParameter {}'.format(k))
    #
    # def get_ion_pressure(self, **kw):
    #     k=''
    #     return self.ask('GetParameter {}'.format(k))
    #
    # def get_convectron_a_pressure(self, **kw):
    #     k=''
    #     return self.ask('GetParameter {}'.format(k))
    #
    # def get_convectron_b_pressure(self, **kw):
    #     k=''
    #     return self.ask('GetParameter {}'.format(k))
# ============= EOF =============================================



