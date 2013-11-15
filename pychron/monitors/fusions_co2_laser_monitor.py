#===============================================================================
# Copyright 2012 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import  List
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.monitors.co2_laser_monitor import CO2LaserMonitor
from pychron.monitors.fusions_laser_monitor import FusionsLaserMonitor
from pychron.remote_hardware.errors.laser_errors import SetpointErrorCode
class FusionsCO2LaserMonitor(FusionsLaserMonitor, CO2LaserMonitor):

    internal_meter_buffer = List

    def update_imb(self, obj, name, old, new):
        if new is not None:
#            self.internal_meter_buffer.append(new)
            self._add_to_buffer(new)

    def stop(self):
        if self.setpoint and self.internal_meter_buffer:
            tol = 4
            if self.internal_meter_buffer:
                if abs(max(self.internal_meter_buffer) - self.setpoint) > tol:
                    self.manager.error_code = SetpointErrorCode(self.setpoint)

        super(FusionsCO2LaserMonitor, self).stop()

    def _fcheck_setpoint(self):
        if self.setpoint:
            self.info('Check setpoint')
            manager = self.manager
            manager.get_laser_watts()
#        self._add_to_buffer(w)

    def _add_to_buffer(self, n):
        trim = 50
        self.internal_meter_buffer.append(n)
        self.internal_meter_buffer = self.internal_meter_buffer[-trim:]
#            avg = sum(self.internal_meter_buffer) / len(self.internal_meter_buffer)
#            if abs(avg - self.setpoint) > self._setpoint_tolerance:
#                pass


#============= EOF =============================================
