# ===============================================================================
# Copyright 2021 ross
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
from traits.api import HasTraits, Instance, Bool

from pychron.hardware.watlow.watlow_ezzone import WatlowEZZone


class TemperatureControllerLaserMixin(HasTraits):
    use_calibrated_temperature = Bool(False)

    def set_laser_output(self, value, units):
        self.debug("set laser output value={} units={}".format(value, units))
        if units == "temp":
            self.set_laser_temperature(value)
        else:
            self.set_laser_power(value, units)

    def set_laser_temperature(self, temp, set_pid=True):
        return self._set_laser_power_hook(temp, mode="closed", set_pid=set_pid)

    def _use_calibrated_temperature_changed(self, new):
        if self.temperature_controller:
            self.temperature_controller.use_calibrated_temperature = new

    def map_temperature(self, v):
        # if self.use_calibrated_temperature:
        v = self.temperature_controller.map_temperature(v)
        return v


class WatlowMixin(TemperatureControllerLaserMixin):
    temperature_controller = Instance(WatlowEZZone)

    def _set_laser_power_hook(self, power, mode="open", set_pid=True, **kw):
        tc = self.temperature_controller
        if tc.control_mode != mode:
            tc.set_control_mode(mode)

        power = float(power)
        if mode == "closed" and set_pid and power:
            tc.set_pid(power)

        func = getattr(tc, "set_{}_loop_setpoint".format(mode))
        func(power, set_pid=set_pid, **kw)

    def emergency_shutoff_hook(self):
        self.temperature_controller.set_control_mode("open")
        self.temperature_controller.set_open_loop_setpoint(0.0)

    def _temperature_controller_default(self):
        w = WatlowEZZone(
            name="temperature_controller",
            use_calibrated_temperature=self.use_calibrated_temperature,
            configuration_dir_name=self.configuration_dir_name,
        )
        return w


# ============= EOF =============================================
