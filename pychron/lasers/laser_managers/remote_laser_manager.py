# ===============================================================================
# Copyright 2019 ross
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
from traits.api import Float, Property, Bool, Button, String, Enum

from pychron.core.ui.thread import Thread
from pychron.globals import globalv
from pychron.lasers.laser_managers.base_lase_manager import BaseLaserManager


class RemoteLaserManager(BaseLaserManager):
    position = String(enter_set=True, auto_set=False)
    x = Property(depends_on='_x')
    y = Property(depends_on='_y')
    z = Property(depends_on='_z')
    _x = Float
    _y = Float
    _z = Float
    connected = Bool
    test_connection_button = Button('Test Connection')
    snapshot_button = Button('Test Snapshot')
    use_autocenter = Bool(False)

    output_power = Float(enter_set=True, auto_set=False)
    fire_laser_button = Button
    fire_label = Property(depends_on='_firing')
    units = Enum('watts', 'percent')

    _patterning = False
    _firing = Bool(False)
    _is_moving = Bool(False)

    stage_stop_button = Button('Stage Stop')
    move_enabled_button = Button('Enable Move')
    move_enabled_label = Property(depends_on='_move_enabled')
    _move_enabled = Bool(False)

    update_position_button = Button

    def open(self, *args, **kw):
        raise NotImplementedError

    def opened(self):
        self.debug('opened')
        if self.update_position():
            self._opened_hook()
            return True

    def update_position(self):
        pos = super(RemoteLaserManager, self).update_position()
        if pos:
            self.trait_set(**dict(zip(('_x', '_y', '_z'), pos)))
            return True

    # private
    def _update_position_button_fired(self):
        if not self.simulation:
            self.update_position()

    def _test_connection_button_fired(self):
        self.test_connection()
        if self.connected:
            self.opened()

    def _test_connection_hook(self):
        pass

    def _test_connection(self):
        if self.simulation:
            return globalv.communication_simulation, None
        else:
            self.connected = False
            if self.setup_communicator():
                self._test_connection_hook()

            self.debug('test connection. connected= {}'.format(self.connected))
            return self.connected, None

    def _position_changed(self):
        if self.position is not None:
            t = Thread(target=self._move_to_position,
                       args=(self.position, self.use_autocenter))
            t.start()
            self._position_thread = t

    def _enable_fired(self):
        if self.enabled:
            self.disable_laser()
            self.enabled = False
        else:
            if self.enable_laser():
                self.enabled = True

    def _get_move_enabled_label(self):
        return 'Enable Axis Moves' if not self._move_enabled else 'Disable Axis Moves'

    def _get_fire_label(self):
        return 'Fire' if not self._firing else 'Stop'

    def _move_enabled_button_fired(self):
        self._move_enabled = not self._move_enabled

    def _opened_hook(self):
        pass

    def _get_x(self):
        return self._x

    def _get_y(self):
        return self._y

    def _get_z(self):
        return self._z
# ============= EOF =============================================
