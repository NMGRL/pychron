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
from traits.api import Any, Instance

from pychron.loggable import Loggable
from pychron.spectrometer.nu.magnet.base import NuMagnet
from pychron.spectrometer.nu.source.base import NuSource


class NuSpectrometer(Loggable):
    magnet = Instance(NuMagnet)
    source = Instance(NuSource)
    magnet_klass = Any
    source_klass = Any
    detector_klass = Any


# ============= EOF =============================================
