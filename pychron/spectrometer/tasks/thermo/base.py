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
from __future__ import absolute_import

from pychron.core.helpers.strtools import to_bool
from pychron.envisage.view_util import open_view
from pychron.spectrometer.readout_view import ReadoutView
from pychron.spectrometer.tasks.base_spectrometer_plugin import BaseSpectrometerPlugin


class ThermoSpectrometerPlugin(BaseSpectrometerPlugin):

    def start(self):
        super(ThermoSpectrometerPlugin, self).start()

        if to_bool(self.application.preferences.get('pychron.spectrometer.auto_open_readout')):
            from pychron.spectrometer.readout_view import new_readout_view

            rv = self.application.get_service(ReadoutView)
            v = new_readout_view(rv)
            open_view(rv, view=v)

# ============= EOF =============================================
