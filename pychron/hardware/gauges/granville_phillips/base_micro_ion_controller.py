# ===============================================================================
# Copyright 2017 Jake Ross
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
# =============enthought library imports=======================
from __future__ import absolute_import
from traits.api import List, Str, HasTraits, Float, Int
# =============standard library imports ========================
from numpy import random, char
import time


# =============local library imports  ==========================
from pychron.hardware.gauges.base_controller import BaseGaugeController


class BaseMicroIonController(BaseGaugeController):
    address = '01'
    mode = 'rs485'

    def load_additional_args(self, config, *args, **kw):
        self.address = self.config_get(config, 'General', 'address', optional=False)
        self.display_name = self.config_get(config, 'General', 'display_name', default=self.name)
        self.mode = self.config_get(config, 'Communications', 'mode', default='rs485')
        self._load_gauges(config)
        return True

    def get_pressures(self, verbose=False):
        kw = {'verbose': verbose, 'force': True}
        b = self.get_convectron_b_pressure(**kw)
        self._set_gauge_pressure('CG2', b)
        time.sleep(0.05)
        a = self.get_convectron_a_pressure(**kw)
        self._set_gauge_pressure('CG1', a)
        time.sleep(0.05)

        ig = self.get_ion_pressure(**kw)
        self._set_gauge_pressure('IG', ig)

        return ig, a, b

    def set_degas(self, state):
        key = 'DG'
        value = 'ON' if state else 'OFF'
        cmd = self._build_command(key, value)
        r = self.ask(cmd)
        r = self._parse_response(r)
        return r

    def get_degas(self):
        key = 'DGS'
        cmd = self._build_command(key)
        r = self.ask(cmd)
        r = self._parse_response(r)
        return r

    def get_ion_pressure(self, **kw):
        name = 'IG'
        return self._get_pressure(name, **kw)

    def get_convectron_a_pressure(self, **kw):
        name = 'CG1'
        return self._get_pressure(name, **kw)

    def get_convectron_b_pressure(self, **kw):
        name = 'CG2'
        return self._get_pressure(name, **kw)

    def set_ion_gauge_state(self, state):
        key = 'IG1'
        value = 'ON' if state else 'OFF'
        cmd = self._build_command(key, value)
        r = self.ask(cmd)
        r = self._parse_response(r)
        return r

    def get_process_control_status(self, channel=None):
        key = 'PCS'

        cmd = self._build_command(key, channel)

        r = self.ask(cmd)
        r = self._parse_response(r)

        if channel is None:
            if r is None:
                # from numpy import random,char
                r = random.randint(0, 2, 6)
                r = ','.join(char.array(r))

            r = r.split(',')
        return r

    def _read_pressure(self, gauge, verbose=False):
        name = gauge.name
        key = 'DS'
        cmd = self._build_command(key, name)

        r = self.ask(cmd, verbose=verbose)
        r = self._parse_response(r, name)
        return r

    def _build_command(self, key, value=None):

        # prepend key with our address
        # example of new string formating
        # see http://docs.python.org/library/string.html#formatspec

        if self.mode == 'rs485':
            key = '#{}{}'.format(self.address, key)

        if value is not None:
            args = (key, value)
        else:
            args = (key,)
        c = ' '.join(args)

        return c

    def _parse_response(self, r, name):
        if self.simulation or r is None:
            from numpy.random import normal

            if name == 'IG':
                loc, scale = 1e-9, 5e-9
            else:
                loc, scale = 1e-2, 5e-3
            return abs(normal(loc, scale))

        return r

# ============= EOF ====================================
