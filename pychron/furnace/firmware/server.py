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

from pychron.headless_loggable import HeadlessLoggable
from pychron.tx.protocols.service import ServiceProtocol


class FurnaceFirmwareProtocol(ServiceProtocol):
    def __init__(self, manager, addr):
        self._manager = manager
        self._addr = addr
        ServiceProtocol.__init__(self)

        misc_services = (('GetLabTemperature', self._manager.get_lab_temperature),
                         ('GetLabHumidity', self._manager.get_lab_humidity),
                         ('SetFrameRate', self._manager.set_frame_rate),
                         ('GetVersion', self._manager.get_version))

        controller_services = (('GetTemperature', self._manager.get_temperature),
                               ('GetSetpoint', self._manager.get_setpoint),
                               ('SetSetpoint', self._manager.set_setpoint),
                               ('GetProcessValue', self._manager.get_process_value),
                               ('GetPercentOutput', self._manager.get_percent_output),
                               ('SetPID', self._manager.set_pid))

        valve_services = (('Open', self._manager.open_switch),
                          ('Close', self._manager.close_switch),
                          ('GetIndicatorState', self._manager.get_indicator_state),
                          ('GetChannelState', self._manager.get_channel_state))

        dump_services = (('LowerFunnel', self._manager.lower_funnel),
                         ('RaiseFunnel', self._manager.raise_funnel),
                         ('InUpPosition', self._manager.is_funnel_up),
                         ('InDownPosition', self._manager.is_funnel_down),
                         ('EnergizeMagnets', self._manager.energize_magnets),
                         ('IsEnergized', self._manager.is_energized),
                         ('DenergizeMagnets', self._manager.denergize_magnets),
                         ('MoveAbsolute', self._manager.move_absolute),
                         ('MoveRelative', self._manager.move_relative),
                         ('GetPosition', self._manager.get_position),
                         ('Slew', self._manager.slew),
                         ('Stalled', self._manager.stalled),
                         ('SetHome', self._manager.set_home),
                         ('StopDrive', self._manager.stop_drive),
                         ('Moving', self._manager.moving),
                         ('StartJitter', self._manager.start_jitter),
                         ('StopJitter', self._manager.stop_jitter))

        self._register_services(misc_services)
        self._register_services(controller_services)
        self._register_services(valve_services)
        self._register_services(dump_services)


class FirmwareFactory(Factory):
    def __init__(self, manager):
        self._manager = manager

    def buildProtocol(self, addr):
        return FurnaceFirmwareProtocol(self._manager, addr)


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

    def add_endpoint(self, port, factory):
        self.debug('add endbpoint port={} factory={}'.format(port, factory.__class__.__name__))
        endpoint = TCP4ServerEndpoint(reactor, port)
        endpoint.listen(factory)

# ============= EOF =============================================
