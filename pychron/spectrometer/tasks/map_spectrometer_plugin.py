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
from pychron.spectrometer.map.spectrometer_manager import MapSpectrometerManager
from pychron.spectrometer.tasks.base_spectrometer_plugin import BaseSpectrometerPlugin


class MapSpectrometerPlugin(BaseSpectrometerPlugin):
    id = 'pychron.spectrometer.map'
    spectrometer_manager_klass = MapSpectrometerManager
    manager_name = 'map_spectrometer_manager'

# ============= EOF =============================================



