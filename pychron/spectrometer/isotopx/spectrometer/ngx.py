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
from traits.api import Enum

from pychron.hardware.isotopx_spectrometer_controller import NGXController
from pychron.pychron_constants import ISOTOPX_DEFAULT_INTEGRATION_TIME, ISOTOPX_INTEGRATION_TIMES, NULL_STR
from pychron.spectrometer.base_spectrometer import BaseSpectrometer
from pychron.spectrometer.isotopx import SOURCE_CONTROL_PARAMETERS
from pychron.spectrometer.isotopx.detector.ngx import NGXDetector
from pychron.spectrometer.isotopx.magnet.ngx import NGXMagnet
from pychron.spectrometer.isotopx.source.ngx import NGXSource


class NGXSpectrometer(BaseSpectrometer):

    integration_time = Enum(ISOTOPX_INTEGRATION_TIMES)

    magnet_klass = NGXMagnet
    detector_klass = NGXDetector
    source_klass = NGXSource
    microcontroller_klass = NGXController

    rcs_id = 'NOM'
    username = 'massspec'
    password = 'analysis'

    def start(self):
        self.ask('Login {},{}'.format(self.username, self.password))
        self.ask('StartAcq -1,{}'.format(self.rcs_id))

    def read_intensities(self):
        keys = []
        signals = []

        datastr = self.read()
        if datastr:
            pass

        return keys, signals

    def read_integration_time(self):
        return self.integration_time

    def set_integration_time(self, it, force=False):
        """

        :param it: float, integration time in seconds
        :param force: set integration even if "it" is not different than self.integration_time
        :return: float, integration time
        """
        # it = normalize_integration_time(it)
        if self.integration_time != it or force:
            self.debug('setting integration time = {}'.format(it))
            self.ask('SetAcqPeriod {}'.format(it*1000))
            self.trait_setq(integration_time=it)

        return it

    def read_parameter_word(self, keys):
        print keys
        values = []
        for kk in keys:
            try:
                key = SOURCE_CONTROL_PARAMETERS[kk]
            except KeyError:
                values.append(NULL_STR)
                continue

            resp = self.ask('GetSourceOutput {}'.format(key))
            if resp is not None:
                try:
                    last_set, readback = resp.split(',')
                    values.append(float(readback))
                except ValueError:
                    values.append(NULL_STR)
        return values

    def _get_simulation_data(self):
        signals = [1, 100, 3, 0.01, 0.01, 0.01]  # + random(6)
        keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
        return keys, signals

    def _integration_time_default(self):
        self.default_integration_time = ISOTOPX_DEFAULT_INTEGRATION_TIME
        return ISOTOPX_DEFAULT_INTEGRATION_TIME

# ============= EOF =============================================
