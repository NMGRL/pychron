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
from __future__ import absolute_import

import time

# ============= local library imports  ==========================
from pychron.hardware.gauges.granville_phillips.micro_ion_controller import MicroIonController


class PychronMicroIonController(MicroIonController):
    def delay_ask(self, *args, **kw):
        time.sleep(0.25)
        return self.ask(*args, **kw)

    def get_pressure(self, name, **kw):
        return self.delay_ask('GetPressure {},{}'.format(self.name, name), **kw)

    def get_ion_pressure(self, **kw):
        return self.delay_ask('GetPressure {},IG'.format(self.name))

    def get_convectron_a_pressure(self, **kw):
        return self.delay_ask('GetPressure {},CG1'.format(self.name))

    def get_convectron_b_pressure(self, **kw):
        return self.delay_ask('GetPressure {},CG2'.format(self.name))


class QtegraMicroIonController(MicroIonController):
    def load_additional_args(self, config, *args, **kw):
        self.warning_dialog('QtegraMicroIonController is deprecated and will be removed soon. Please use '
                            'QtegraGaugeController instead')

        self.display_name = self.config_get(config, 'General', 'display_name', default=self.name)
        self._load_gauges(config)
        return True

    def get_pressures(self, verbose=False):
        for g in self.gauges:
            ig = self.ask('GetParameter {}'.format(g.name), verbose=verbose, force=True)
            self._set_gauge_pressure(g.name, ig)

# ============= EOF =============================================



