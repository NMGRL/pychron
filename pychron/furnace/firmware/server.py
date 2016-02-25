# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory
from pychron.loggable import Loggable
from pychron.tx.protocols.service import ServiceProtocol


class FurnaceFirmwareProtocol(ServiceProtocol):
    def __init__(self, manager, addr):
        self._manager = manager
        self._addr = addr
        ServiceProtocol.__init__(self)

        get_services = (('GetTemperature', self._manager.get_temperature),
                        ('GetSetpoint', self._manager.get_setpoint),
                        ('GetPosition', self._manager.get_position),
                        ('GetMagnetsState', self._manager.get_magnets_state),
                        ('Moving', self._manager.moving),
                        ('IsFunnelUp',self._manager.is_funnel_up),
                        ('IsFunnelDown', self._manager.is_funnel_down),
                        ('GetChannelState', self._manager.get_channel_state))

        set_services = (('SetSetpoint', self._manager.set_setpoint),
                        ('SetPosition', self._manager.set_position),
                        ('Open', self._manager.open_switch),
                        ('Close', self._manager.close_switch),
                        ('LowerFunnel', self._manager.lower_funnel),
                        ('RaiseFunnel', self._manager.raise_funnel),
                        ('EnergizeMagnets', self._manager.energize_magnets),
                        ('DenergizeMagnets', self._manager.denergize_magnets),
                        ('MoveAbsolute', self._manager.move_absolute),
                        ('MoveRelative', self._manager.move_relative))

        self._register_services(get_services)
        self._register_services(set_services)


class FirmwareFactory(Factory):
    def __init__(self, manager):
        self._manager = manager

    def buildProtocol(self, addr):
        if self.protocol_klass is None:
            raise NotImplementedError

        return FurnaceFirmwareProtocol(self._manager, addr)


class FirmwareServer(Loggable):
    manager = Instance('pychron.furnace.firmware.manager.FirmwareManager')

    def bootstrap(self, port=None, **kw):
        self._load_config(port)
        reactor.run()

    def _load_config(self, port):
        if port is None:
            port = 8000
        self.add_endpoint(port, FirmwareFactory(self.manager))

    def add_endpoint(self, port, factory):
        endpoint = TCP4ServerEndpoint(reactor, port)
        endpoint.listen(factory)

# ============= EOF =============================================
