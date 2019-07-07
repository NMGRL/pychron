# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import
from pychron.hardware.isotopx_spectrometer_controller import NGXController
from pychron.spectrometer.isotopx.manager.ngx import NGXSpectrometerManager
from pychron.spectrometer.tasks.isotopx.base import IsotopxSpectrometerPlugin
from pychron.spectrometer.tasks.isotopx.task import IsotopxSpectrometerTask
from pychron.spectrometer.tasks.spectrometer_preferences import NGXSpectrometerPreferencesPane, \
    SpectrometerPreferencesPane


class NGXSpectrometerPlugin(IsotopxSpectrometerPlugin):
    id = 'pychron.spectrometer.ngx'
    spectrometer_manager_klass = NGXSpectrometerManager
    manager_name = 'ngx_spectrometer_manager'
    name = 'NGXSpectrometer'
    task_klass = IsotopxSpectrometerTask

    def _preferences_panes_default(self):
        return [SpectrometerPreferencesPane, NGXSpectrometerPreferencesPane]

    def _controller_factory(self):
        ngx = NGXController(name='spectrometer_microcontroller')
        ngx.bootstrap()
        return ngx

    def _service_offers_default(self):
        sos = super(NGXSpectrometerPlugin, self)._service_offers_default()
        if sos:
            so = self.service_offer_factory(factory=self._controller_factory,
                                        protocol=NGXController)
            sos.append(so)

        return sos
