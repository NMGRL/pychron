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
from traits.api import Str, CInt, Enum
from zaber.serial import BinarySerial, BinaryDevice

# from zaber_motion import Library

# Library.enable_device_db_store()

from pychron.hardware.motion_controller import MotionController
from pychron.hardware.zaber.axis import ZaberAxis


# from zaber_motion import Units
#
#
# class AsciiWrapper:
#     def __init__(self, devices):
#         self._device = devices[0]
#
#     def get_axis(self, a):
#         return self._device.get_axis(a)
#
#     def is_busy(self):
#         return self._device.all_axes.is_busy()
#
#
# class BinaryWrapper:
#     def __init__(self, devices):
#         self._devices = devices
#
#     def get_axis(self, a):
#         return self._devices[a]
#
#     def is_busy(self):
#         return any((d.is_busy() for d in self._devices))


class LegacyBinaryZaberMotionController(MotionController):
    port = Str
    device_id = CInt
    baudrate = CInt
    _device = None
    # _units = Units.LENGTH_MILLIMETRES
    # _wrapper = None

    def load(self, *args, **kw):

        config = self.get_configuration()
        if config:
            section = "Communications"
            self.set_attribute(config, "port", section, "port")
            self.set_attribute(
                config, "device_id", section, "device_id", optional=True, default=0
            )
            self.set_attribute(
                config, "baudrate", section, "baudrate", optional=True, default=9600
            )

            self.axes_factory(config)

            return True

    def initialize(self, *args, **kw):
        return True

    def open(self, *args, **kw):
        self.debug("scanning port {}".format(self.port))
        bs = BinarySerial(self.port, timeout=200, inter_char_timeout=2)

        for a in self.axes.values():
            a.device = BinaryDevice(bs, a.device_id)

        return True

    def _get_simulation(self):
        return False

    def linear_move(self, x, y, block=True, *args, **kw):
        if kw.get("source") != "laser_canvas":
            xaxis = self.single_axis_move("x", x, block=False)
            yaxis = self.single_axis_move("y", y, block=False)
            self.update_axes()

    def single_axis_move(self, key, value, block=True, *args, **kw):
        axis = self.axes[key]
        steps = axis.convert_to_steps(value)
        self.debug("calculated steps={} value={}".format(steps, value))
        axis.device.move_abs(steps)
        if block:
            self.update_axes()
        return axis

    def home(self, axes, block=True, *args, **kw):
        for a in self.axes.values():
            if a.name in axes:
                a.device.home()
            #     axis = self._wrapper.get_axis(a.device_id)
            #     axis.home(wait_until_idle=block)

    def get_current_position(self, key, *args, **kw):
        axis = self.axes[key]
        return axis.get_position()

    def _moving(self, axis=None, verbose=False):
        # if axis is None:
        #     moving = self._wrapper.is_busy()
        # else:
        #     axis = self._get_device_axis(axis)
        #     moving = axis.is_busy()

        return False

    def _axis_factory(self, path, **kw):
        a = ZaberAxis(parent=self, **kw)
        a.load(path)
        return a


# class ZaberMotionController(MotionController):
#     port = Str
#     device_id = CInt
#     baudrate = CInt
#     protocol = Enum('ASCII', 'Binary')
#     _device = None
#     _units = Units.LENGTH_MILLIMETRES
#     _wrapper = None
#     move_enabled = False
#
#     def load(self, *args, **kw):
#         config = self.get_configuration()
#         if config:
#             section = 'Communications'
#             self.set_attribute(config, 'port', section, 'port')
#             self.set_attribute(config, 'device_id', section, 'device_id', optional=True, default=0)
#             self.set_attribute(config, 'baudrate', section, 'baudrate', optional=True, default=9600)
#             self.set_attribute(config, 'protocol', section, 'protocol', optional=True, default='ASCII')
#
#             self.axes_factory(config)
#
#             return True
#
#     def initialize(self, *args, **kw):
#         return True
#
#     def open(self, *args, **kw):
#         self.debug('scanning port {}'.format(self.port))
#         if self.protocol == 'ASCII':
#             from zaber_motion.ascii import Connection
#         else:
#             from zaber_motion.binary import Connection
#
#         connection = Connection.open_serial_port(self.port, self.baudrate)
#         device_list = connection.detect_devices()
#         self.debug(device_list)
#         if self.protocol == 'ASCII':
#             klass = AsciiWrapper
#         else:
#             klass = BinaryWrapper
#
#         self._wrapper = klass(device_list)
#         return True
#
#     def _get_simulation(self):
#         return False
#
#     def linear_move(self, x, y, block=True, *args, **kw):
#         xaxis = self.single_axis_move('x', x, block=False)
#         yaxis = self.single_axis_move('y', y, block=False)
#
#         if block:
#             if self.protocol == 'ASCII':
#                 xaxis.wait_until_idle()
#                 yaxis.wait_until_idle()
#             else:
#                 while 1:
#                     if not xaxis.is_busy() and not yaxis.is_busy():
#                         return
#
#     def single_axis_move(self, key, value, block=True, *args, **kw):
#         axis = self._get_device_axis(key)
#
#         if self.move_enabled:
#             if self.protocol == 'ASCII':
#                 axis.move_absolute(value, self._units, wait_until_idle=block)
#             else:
#                 axis.move_absolute(value, self._units)
#
#         return axis
#
#     def home(self, axes, block=True, *args, **kw):
#         for a in self.axes.values():
#             if a.name in axes:
#                 axis = self._wrapper.get_axis(a.device_id)
#                 axis.home(wait_until_idle=block)
#
#     def get_current_position(self, axis, *args, **kw):
#         axis = self._get_device_axis(axis)
#         return axis.get_position(self._units)
#
#     def _moving(self, axis=None, verbose=False):
#         if axis is None:
#             moving = self._wrapper.is_busy()
#         else:
#             axis = self._get_device_axis(axis)
#             moving = axis.is_busy()
#
#         return moving
#
#     def _get_device_axis(self, aid):
#         if isinstance(aid, str):
#             aid = self.axes[aid].device_id
#
#         return self._wrapper.get_axis(aid)
#
#     def _axis_factory(self, path, **kw):
#         a = ZaberAxis(parent=self, **kw)
#         a.load(path)
#         return a
# ============= EOF =============================================
