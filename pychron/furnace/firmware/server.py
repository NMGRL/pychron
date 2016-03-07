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
from twisted.internet.protocol import Factory, Protocol

from pychron.headless_loggable import HeadlessLoggable
from pychron.tx.protocols.service import ServiceProtocol


class FurnaceFirmwareProtocol(ServiceProtocol):
    def __init__(self, manager, addr):
        self._manager = manager
        self._addr = addr
        ServiceProtocol.__init__(self)

        misc_services = (('GetLabTemperature', self._manager.get_lab_temperature),
                         ('GetLabHumidity', self._manager.get_lab_humidity),
                         ('GetImageArray', self._manager.get_image_array))

        controller_services = (('GetTemperature', self._manager.get_temperature),
                               ('GetSetpoint', self._manager.get_setpoint),
                               ('SetSetpoint', self._manager.set_setpoint))

        valve_services = (('Open', self._manager.open_switch),
                          ('Close', self._manager.close_switch),
                          ('GetIndicatorState', self._manager.get_indicator_state),
                          ('GetChannelState', self._manager.get_channel_state))

        dump_services = (('LowerFunnel', self._manager.lower_funnel),
                         ('RaiseFunnel', self._manager.raise_funnel),
                         ('EnergizeMagnets', self._manager.energize_magnets),
                         ('IsEnergized', self._manager.is_energized),
                         ('DenergizeMagnets', self._manager.denergize_magnets),
                         ('MoveAbsolute', self._manager.move_absolute),
                         ('MoveRelative', self._manager.move_relative),
                         ('GetPosition', self._manager.get_position),
                         ('Slew', self._manager.slew),
                         ('StopDrive', self._manager.stop_drive),
                         ('Moving', self._manager.moving),
                         ('StartJitter', self._manager.start_jitter),
                         ('StopJitter', self._manager.stop_jitter))

        self._register_services(misc_services)
        self._register_services(controller_services)
        self._register_services(valve_services)
        self._register_services(dump_services)


class Producer:
    def __init__(self, proto, manager):
        self._proto = proto
        self._manager = manager
        self._paused = False

    def pauseProducing(self):
        self._paused = True

    def resumeProducing(self):
        self._paused = False
        self._alive = True
        img = self._manager.get_image_array()
        imstr = img.dumps()
        n = len(imstr)
        imstr = '{:08X}{}'.format(len(imstr), imstr)

        rem = n % 4096
        for ci in xrange(0, n, 4096):
            try:
                self._proto.transport.write(imstr[ci:ci + 4096])
            except IndexError:
                pass
            if not self._alive:
                return

        self._proto.transport.write(imstr[ci:ci + rem])
        self._proto.transport.unregisterProducer()
        self._proto.transport.loseConnection()

    def stopProducing(self):
        self._alive = False


class FirmwareCameraProtocol(Protocol):
    def __init__(self, manager, addr):
        self._manager = manager
        self._addr = addr

    def dataReceived(self, data):
        producer = Producer(self, self._manager)
        self.transport.registerProducer(producer, True)
        producer.resumeProducing()


class FirmwareFactory(Factory):
    def __init__(self, manager):
        self._manager = manager

    def buildProtocol(self, addr):
        return FurnaceFirmwareProtocol(self._manager, addr)


class FirmwareCameraFactory(Factory):
    def __init__(self, manager):
        self._manager = manager

    def buildProtocol(self, addr):
        return FirmwareCameraProtocol(self._manager, addr)


class FirmwareServer(HeadlessLoggable):
    manager = Instance('pychron.furnace.firmware.manager.FirmwareManager')

    def bootstrap(self, port=None, **kw):
        self.debug('bootstrap')
        self._load_config(port)

        self.debug('starting reactor')
        reactor.run()

    def _load_config(self, port):
        self.debug('load config')
        if port is None:
            port = 8000
        self.add_endpoint(port, FirmwareFactory(self.manager))
        self.add_endpoint(port + 1, FirmwareCameraFactory(self.manager))

    def add_endpoint(self, port, factory):
        self.debug('add endbpoint port={} factory={}'.format(port, factory.__class__.__name__))
        endpoint = TCP4ServerEndpoint(reactor, port)
        endpoint.listen(factory)

# ============= EOF =============================================
