# ===============================================================================
# Copyright 2011 Jake Ross
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
from pychron.hardware.thermo_spectrometer_controller import ArgusController
from pychron.spectrometer.thermo.detector.argus import ArgusDetector
from pychron.spectrometer.thermo.magnet.argus import ArgusMagnet
from pychron.spectrometer.thermo.source.argus import ArgusSource
from pychron.spectrometer.thermo.spectrometer.base import ThermoSpectrometer


class ArgusSpectrometer(ThermoSpectrometer):
    """
    Interface to a Thermo Scientific Argus Mass Spectrometer via Qtegra and RemoteControlServer.cs
    magnet control provided by ArgusMagnet
    source control provided by ArgusSource

    direct access to RemoteControlServer.cs API via microcontroller
    e.g. microcontroller.ask('GetIntegrationTime')
    """
    magnet_klass = ArgusMagnet
    source_klass = ArgusSource
    detector_klass = ArgusDetector
    microcontroller_klass = ArgusController
# ============= EOF =============================================
