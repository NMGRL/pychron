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

        misc_services = (('GetLabTemperature', manager.get_lab_temperature),
                         ('GetLabHumidity', manager.get_lab_humidity),
                         ('SetFrameRate', manager.set_frame_rate),
                         ('GetVersion', manager.get_version),
                         ('GetDIState', manager.get_di_state),
                         ('GetHeartBeat', manager.get_heartbeat),
                         ('GetFullSummary', manager.get_full_summary))

        controller_services = (('GetTemperature', manager.get_temperature),
                               ('GetSetpoint', manager.get_setpoint),
                               ('SetSetpoint', manager.set_setpoint),
                               ('GetProcessValue', manager.get_process_value),
                               ('GetPercentOutput', manager.get_percent_output),
                               ('GetFurnaceSummary', manager.get_furnace_summary),
                               ('SetPID', manager.set_pid))

        valve_services = (('Open', manager.open_switch),
                          ('Close', manager.close_switch),
                          ('GetIndicatorState', manager.get_indicator_state),
                          ('GetChannelDOState', manager.get_channel_do_state),
                          ('GetChannelState', manager.get_channel_state),
                          ('GetIndicatorComponentStates', manager.get_indicator_component_states))

        dump_services = (('LowerFunnel', manager.lower_funnel),
                         ('RaiseFunnel', manager.raise_funnel),
                         ('InUpPosition', manager.is_funnel_up),
                         ('InDownPosition', manager.is_funnel_down),
                         ('EnergizeMagnets', manager.energize_magnets),
                         ('IsEnergized', manager.is_energized),
                         ('DenergizeMagnets', manager.denergize_magnets),
                         ('MoveAbsolute', manager.move_absolute),
                         ('MoveRelative', manager.move_relative),
                         ('GetPosition', manager.get_position),
                         ('Slew', manager.slew),
                         ('Stalled', manager.stalled),
                         ('SetHome', manager.set_home),
                         ('StopDrive', manager.stop_drive),
                         ('Moving', manager.moving),
                         ('StartJitter', manager.start_jitter),
                         ('StopJitter', manager.stop_jitter))

        bakeout_services = (('GetSetpoint', manager.get_bakeout_setpoint),
                            ('SetSetpoint', manager.set_bakeout_setpoint),
                            ('GetTempPower', manager.get_bakeout_temp_and_power))

        gauge_services = (('GetPressure', manager.get_gauge_pressure),)
        for s in (misc_services, controller_services, valve_services, dump_services,
                  bakeout_services, gauge_services):
            self._register_services(s)


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
