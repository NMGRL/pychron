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
from twisted.internet.protocol import Factory
# ============= local library imports  ==========================
from pychron.tx.protocols.valve import ValveProtocol
from pychron.tx.protocols.laser import LaserProtocol


class LaserFactory(Factory):
    _name = None

    def __init__(self, application):
        self._app = application

    def buildProtocol(self, addr):
        if self._name is None:
            raise NotImplementedError
        return LaserProtocol(self._app, self._name, addr)


class FusionsCO2Factory(LaserFactory):
    _name = 'FusionsCO2'


class FusionsDiodeFactory(LaserFactory):
    _name = 'FusionsDiode'


class FusionsUVFactory(LaserFactory):
    _name = 'FusionsUV'


class ValveFactory(Factory):
    def __init__(self, application=None):
        self._app = application

    def buildProtocol(self, addr):
        return ValveProtocol(self._app, addr)

# ============= EOF =============================================
