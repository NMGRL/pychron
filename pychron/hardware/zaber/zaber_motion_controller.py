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
from traits.api import Str, Int
from pychron.hardware.motion_controller import MotionController
from zaber_motion import Connection, Units


class ZaberMotionController(MotionController):
    port = Str
    device_id = Int
    _device = None
    _units = Units.LENGTH_MILLIMETERS

    def load(self, *args, **kw):
        config = self.get_configuration()
        if config:
            section = 'Communications'
            self.set_attribute(config, section, 'port')
            self.set_attribute(config, section, 'device_id', optional=True, default=0)

    def open(self, *args, **kw):
        connection = Connection.open_serial_port(self.port)
        device_list = connection.detect_devices()
        self._device = device_list[self.device_id]

    def linear_move(self, x, y, block=True, *args, **kw):
        xaxis = self.single_axis_move('x', x, block=False)
        yaxis = self.single_axis_move('y', y, block=False)

        if block:
            xaxis.wait_until_idle()
            yaxis.wait_until_idle()

    def single_axis_move(self, key, value, block=True, *args, **kw):
        axis = self._get_device_axis(key)
        axis.move_absolute(value, self._units, wait_until_idle=block)
        return axis

    def home(self, axes, block=True, *args, **kw):
        for a in self.axes.values():
            if a.name in axes:
                axis = self._device.get_axis(a.id)
                axis.home(wait_until_idle=block)

    def get_current_position(self, axis, *args, **kw):
        axis = self._get_device_axis(axis)
        return axis.get_position(self._units)

    def _moving(self, axis=None, verbose=False):
        if axis is None:
            moving = self._device.all_axes.is_busy()
        else:
            axis = self._get_device_axis(axis)
            moving = axis.is_busy()

        return moving

    def _get_device_axis(self, aid):
        if isinstance(aid, str):
            aid = self.axes[aid].id

        return self._device.get_axis(aid)

# ============= EOF =============================================
