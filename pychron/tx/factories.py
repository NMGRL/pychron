# ===============================================================================
# Copyright 2015 Jake Ross
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
import io
import os

from twisted.internet.protocol import Factory
from twisted.logger import Logger
from twisted.logger import jsonFileLogObserver

from pychron.tx.protocols.aqua import AquAProtocol
from pychron.tx.protocols.furnace import FurnaceProtocol
from pychron.tx.protocols.laser import LaserProtocol
from pychron.tx.protocols.valve import ValveProtocol


class LaserFactory(Factory):
    _name = None

    def __init__(self, application):
        self._app = application

    def buildProtocol(self, addr):
        if self._name is None:
            raise NotImplementedError
        return LaserProtocol(self._app, self._name, addr, None)


class FusionsCO2Factory(LaserFactory):
    _name = "FusionsCO2"


class FusionsDiodeFactory(LaserFactory):
    _name = "FusionsDiode"


class FusionsUVFactory(LaserFactory):
    _name = "FusionsUV"


class OsTechDiodeFactory(LaserFactory):
    _name = "OsTechDiode"


from pychron.paths import paths

path = os.path.join(paths.log_dir, "pps.log.json")
logger = Logger(observer=jsonFileLogObserver(io.open(path, "w")))


class BaseFactory(Factory):
    protocol_klass = None

    def __init__(self, application=None):
        self._app = application

    def buildProtocol(self, addr):
        if self.protocol_klass is None:
            raise NotImplementedError

        return self.protocol_klass(self._app, addr, logger)


class ValveFactory(BaseFactory):
    protocol_klass = ValveProtocol


class FurnaceFactory(BaseFactory):
    protocol_klass = FurnaceProtocol


class AquAFactory(BaseFactory):
    protocol_klass = AquAProtocol


# ============= EOF =============================================
