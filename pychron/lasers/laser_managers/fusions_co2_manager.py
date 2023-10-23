# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# =============enthought library imports=======================
from __future__ import absolute_import
from traits.api import Button, DelegatesTo

from .fusions_laser_manager import FusionsLaserManager
from pychron.hardware.fusions.fusions_co2_logic_board import FusionsCO2LogicBoard
from pychron.monitors.fusions_co2_laser_monitor import FusionsCO2LaserMonitor
from pychron.response_recorder import ResponseRecorder


class FusionsCO2Manager(FusionsLaserManager):
    """ """

    stage_manager_id = "fusions.co2"
    name = "FusionsCO2"
    id = "pychron.fusions.co2"

    launch_profile = Button
    launch_step = Button

    request_power = DelegatesTo("laser_controller")
    request_powermin = DelegatesTo("laser_controller")
    request_powermax = DelegatesTo("laser_controller")

    monitor_name = "co2_laser_monitor"
    monitor_klass = FusionsCO2LaserMonitor

    # dbname = paths.co2laser_db
    # db_root = paths.co2laser_db_root

    _stop_signal = None

    configuration_dir_name = "fusions_co2"

    def get_laser_watts(self):
        return self.laser_controller.read_power_meter()

    def set_laser_power_hook(self, rp, **kw):
        """ """
        self.laser_controller.set_laser_power(rp, **kw)
        if self.monitor:
            self.monitor.setpoint = self._requested_power
        else:
            self.debug("no monitor")

        if self.data_manager:
            with self._data_manager_lock:
                tab = self.data_manager.get_table("internal", "Power")
                if tab:
                    tab.attrs.request_power = rp

    def _laser_controller_default(self):
        """ """
        b = FusionsCO2LogicBoard(
            name="laser_controller",
            configuration_name="laser_controller",
            configuration_dir_name=self.configuration_dir_name,
        )
        return b

    def _response_recorder_default(self):
        r = ResponseRecorder(
            response_device=self.laser_controller, output_device=self.laser_controller
        )
        return r


if __name__ == "__main__":
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.envisage.initialization.initializer import Initializer

    from launchers.helpers import build_version

    build_version("_test")
    logging_setup("fusions co2")
    f = FusionsCO2Manager()
    f.use_video = True
    f.record_brightness = True
    ini = Initializer()

    a = dict(manager=f, name="FusionsCO2")
    ini.add_initialization(a)
    ini.run()
    #    f.bootstrap()
    f.configure_traits()

#    def show_streams(self):
#        '''
#        '''
#
#
#        if not self.streaming:
#
#        tc = self.temperature_controller
#        pyro = self.pyrometer
#        tm = self.temperature_monitor
#        apm = self.analog_power_meter
#        avaliable_streams = [apm]
#        self._show_streams_(avaliable_streams)

#
#    def get_menus(self):
#        '''
#        '''
#        m = super(FusionsCO2Manager, self).get_menus()
#
#
#
#        m += [('Calibration', [
#                               dict(name = 'Power Profile', action = 'launch_power_profile'),
#                                  ]
#                                ),
#
#                ]
#        return m
# ============= EOF ====================================
