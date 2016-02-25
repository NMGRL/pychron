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
from threading import Thread

import yaml
# ============= standard library imports ========================
# ============= local library imports  ==========================
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory

from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.tx.protocols.service import ServiceProtocol


class FurnaceFirmwareProtocol(ServiceProtocol):
    def __init__(self, manager, addr):
        self._manager = manager
        self._addr = addr
        ServiceProtocol.__init__(self)

        get_services = (('GetTemperature', '_get_temperature'),
                        ('GetSetpoint', '_get_setpoint'),
                        ('GetPosition', '_get_position'),
                        ('GetMagnetsState', '_get_magnets_state'))

        set_services = (('SetSetpoint', '_set_setpoint'),
                        ('SetPosition', '_set_position'),
                        ('Open', '_open_switch'),
                        ('Close', '_close_switch'),
                        ('LowerFunnel', '_lower_funnel'),
                        ('RaiseFunnel', '_raise_funnel'),
                        ('EnergizeMagnets', '_energize_magnets'),
                        ('DenergizeMagnets', '_denergize_magnets'),
                        ('MoveAbsolute', '_move_absolute'),
                        ('MoveRelative', '_move_relative'),
                        )

        self._register_services(get_services)
        self._register_services(set_services)

    # service handlers
    # getters
    def _get_temperature(self, data):
        return self._manager.get_temperature()

    def _get_setpoint(self, data):
        return self._manager.get_temperature()

    def _get_position(self, data):
        return self._manager.get_position(data)

    def _get_dump_state(self):
        return self._manager.get_dump_state()

    # setters
    def _set_setpoint(self, data):
        return self._manager.set_setpoint(data)

    def _set_position(self, data):
        return self._manager.set_position(data)

    def _open_switch(self, data):
        return self._manager.open_switch(data)

    def _close_switch(self, data):
        return self._manager.close_switch(data)

    def _lower_funnel(self, data):
        return self._manager.lower_funnel()

    def _raise_funnel(self, data):
        return self._manager.raise_funnel()

    def _energize_magnets(self, data):
        return self._manager.energize_magnets()

    def _denergize_magnets(self, data):
        return self._manager.denergize_magnets()

    def _move_relative(self, data):
        return self._manager.move_relative(data)

    def _move_absolute(self, data):
        return self._manager.move_absolute(data)


class FirmwareFactory(Factory):
    def __init__(self, manager):
        self._manager = manager

    def buildProtocol(self, addr):
        if self.protocol_klass is None:
            raise NotImplementedError

        return FurnaceFirmwareProtocol(self._manager, addr)


class FirmwareServer(Loggable):
    def bootstrap(self, port=None, **kw):
        self._load_config(port)
        self._serve()

    def _load_config(self, port):
        if port is None:
            port = 8000
        self.add_endpoint(port, FirmwareFactory)

        with open(paths.furnace_firmware, 'r') as rfile:
            yd = yaml.load(rfile)
            # for endpoint in yd:
            #     factory = FACTORIES.get(endpoint['factory'])
            #     self.add_endpoint(endpoint['port'], factory)

    def _serve(self):
        t = Thread(target=reactor.run, args=(False,))
        t.setDaemon(True)
        t.start()

    def add_endpoint(self, port, factory):
        endpoint = TCP4ServerEndpoint(reactor, port)
        endpoint.listen(factory)

# ============= EOF =============================================
