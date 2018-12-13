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
from __future__ import absolute_import
import os

from traits.api import Any, DelegatesTo, Property

from pychron.managers.manager import Manager
from pychron.paths import paths


class BaseSpectrometerManager(Manager):
    spectrometer = Any
    spectrometer_klass = None
    simulation = DelegatesTo('spectrometer')
    name = Property(depends_on='spectrometer')

    def __init__(self, application, *args, **kw):
        self.application = application
        super(BaseSpectrometerManager, self).__init__(*args, **kw)

    def read_trap_current(self):
        return self.spectrometer.source.read_trap_current()

    def read_emission(self):
        return self.spectrometer.source.read_emission()

    def test_connection(self, **kw):
        return self.spectrometer.test_connection(**kw)

    def test_intensity(self, **kw):
        return self.spectrometer.test_intensity(**kw)

    def make_gains_dict(self):
        return self.spectrometer.make_gains_dict()

    def make_configuration_dict(self):
        return self.spectrometer.make_configuration_dict()

    def make_deflections_dict(self):
        return self.spectrometer.make_deflection_dict()

    def send_configuration(self):
        if self.spectrometer:
            self.spectrometer.send_configuration()

    def reload_mftable(self):
        self.spectrometer.magnet.reload_field_table()

    def protect_detector(self, det, protect):
        pass

    def set_deflection(self, det, defl):
        pass

    def bind_preferences(self):
        pass

    def load(self):
        spec = self.spectrometer
        self.debug('******************************* LOAD Spec')
        spec.load()
        return True

    def finish_loading(self):
        self.debug('Finish loading')

        # integration_time = 1.048576

        # set device microcontrollers
        # self.spectrometer.set_microcontroller(self.spectrometer_microcontroller)
        # self.spectrometer.set_microcontroller()

        # update the current hv
        self.spectrometer.source.sync_parameters()

        # set integration time
        self.spectrometer.get_integration_time()
        # integration_time = self.spectrometer.get_integration_time()
        # self.integration_time = integration_time

        # self.integration_time = 0.065536

        self.spectrometer.load_configurations()

        self.bind_preferences()
        self.spectrometer.finish_loading()

    def _get_name(self):
        r = ''
        if self.spectrometer:
            if self.spectrometer.microcontroller:
                r = self.spectrometer.microcontroller.name
        return r

    def _spectrometer_default(self):
        return self.spectrometer_klass(application=self.application)

# ============= EOF =============================================
