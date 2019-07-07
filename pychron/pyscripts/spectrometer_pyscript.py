# ===============================================================================
# Copyright 2017 ross
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
from __future__ import absolute_import

import yaml

from pychron.paths import paths
from pychron.pyscripts.pyscript import PyScript, count_verbose_skip, makeRegistry

command_register = makeRegistry()


class SpectrometerPyScript(PyScript):
    def get_command_register(self):
        cs = super(SpectrometerPyScript, self).get_command_register()
        return cs + list(command_register.commands.items())

    @count_verbose_skip
    @command_register
    def position_magnet(self, isotope='', detector='', calc_time=False):
        if calc_time:
            return

        self._manager_actions([('spy_position_magnet', (isotope, detector), {})])

    @count_verbose_skip
    @command_register
    def peak_center(self, config_name='default', calc_time=False):
        if calc_time:
            n = 31
            self._estimated_duration += n * 2
            return

        return self._manager_actions([('spy_peak_center', (config_name,), {})])[0]

    @count_verbose_skip
    @command_register
    def adjust_af_demag(self, period='', frequency='', duration='', start_amplitude='', calc_time=False):
        if calc_time:
            return

        with open(paths.af_demagnetization, 'r') as rfile:
            yd = yaml.load(rfile)

        if period:
            yd['period'] = period
        if frequency:
            yd['frequency'] = frequency
        if duration:
            yd['duration'] = duration
        if start_amplitude:
            yd['start_amplitude'] = start_amplitude

        with open(paths.af_demagnetization, 'w') as wfile:
            yaml.dump(yd, wfile)

# ============= EOF =============================================
