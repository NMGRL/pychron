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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory

from pychron.furnace.firmware.manager import FirmwareManager
from pychron.headless_loggable import HeadlessLoggable
from pychron.tx.protocols.service import ServiceProtocol


class FurnaceFirmwareProtocol(ServiceProtocol):
    def __init__(self, manager, addr):
        self._manager = manager
        self._addr = addr
        ServiceProtocol.__init__(self)

        misc_services = (('GetLabTemperature', 'get_lab_temperature'),
                         ('GetLabHumidity', 'get_lab_humidity'),
                         ('SetFrameRate', 'set_frame_rate'),
                         ('GetVersion', 'get_version'),
                         ('GetDIState', 'get_di_state'),
                         ('GetHeartBeat', 'get_heartbeat'),
                         ('GetFullSummary', 'get_full_summary'))

        controller_services = (('GetTemperature', 'get_temperature'),
                               ('GetSetpoint', 'get_setpoint'),
                               ('SetSetpoint', 'set_setpoint'),
                               ('GetProcessValue', 'get_temperature'),
                               ('GetPercentOutput', 'get_percent_output'),
                               ('GetFurnaceSummary', 'get_furnace_summary'),
                               ('SetPID', 'set_pid'))

        valve_services = (('Open', 'open_switch'),
                          ('Close', 'close_switch'),
                          ('GetIndicatorState', 'get_indicator_state'),
                          # ('GetChannelDOState', 'get_channel_do_state'),
                          ('GetChannelState', 'get_channel_state'),
                          ('GetIndicatorComponentStates', 'get_indicator_component_states'))

        dump_services = (('LowerFunnel', 'lower_funnel'),
                         ('RaiseFunnel', 'raise_funnel'),
                         ('InUpPosition', 'is_funnel_up'),
                         ('InDownPosition', 'is_funnel_down'),
                         ('EnergizeMagnets', 'energize_magnets'),
                         ('IsEnergized', 'is_energized'),
                         ('RotaryDumperMoving', 'rotary_dumper_moving'),
                         ('DenergizeMagnets', 'denergize_magnets'),
                         ('MoveAbsolute', 'move_absolute'),
                         ('MoveRelative', 'move_relative'),
                         ('GetPosition', 'get_position'),
                         ('Slew', 'slew'),
                         ('Stalled', 'stalled'),
                         ('SetHome', 'set_home'),
                         ('StopDrive', 'stop_drive'),
                         ('Moving', 'moving'),
                         ('StartJitter', 'start_jitter'),
                         ('StopJitter', 'stop_jitter'))

        bakeout_services = (('GetBakeoutSetpoint', 'get_bakeout_setpoint'),
                            ('SetBakeoutControlMode', 'set_bakeout_control_mode'),
                            ('GetBakeoutTemperature', 'get_bakeout_temperature'),
                            ('SetBakeoutClosedLoopSetpoint', 'set_bakeout_setpoint'),
                            ('GetBakeoutTempPower', 'get_bakeout_temp_and_power'))

        gauge_services = (('GetPressure', 'get_gauge_pressure'),)
        for s in (misc_services, controller_services, valve_services, dump_services,
                  bakeout_services, gauge_services):
            s = [(name, getattr(manager, cb)) for name, cb in s]
            self._register_services(s)


class FirmwareFactory(Factory):
    def __init__(self, manager):
        self._manager = manager

    def buildProtocol(self, addr):
        return FurnaceFirmwareProtocol(self._manager, addr)


class FirmwareServer(HeadlessLoggable):
    def bootstrap(self, port=None, **kw):
        self.debug('bootstrap')
        self._load_config(port)

        self.debug('starting reactor')
        reactor.run()

    def _load_config(self, port):
        self.debug('load config')
        if port is None:
            port = 8000

        manager = FirmwareManager()
        manager.bootstrap()
        factory = FirmwareFactory(manager)

        self.debug('add endpoint port={} factory={}'.format(port, factory.__class__.__name__))
        endpoint = TCP4ServerEndpoint(reactor, port)
        endpoint.listen(factory)

# ============= EOF =============================================
