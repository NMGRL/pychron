# ===============================================================================
# Copyright 2015 Jake Ross
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
import os
import pickle
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, Instance, CInt
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.hardware.linear_mapper import LinearMapper
from pychron.core.helpers.timer import Timer
from pychron.loggable import Loggable
from pychron.paths import paths


class BaseLinearDrive(Loggable):
    velocity = Property
    _velocity = Float
    acceleration = Float

    nominal_position = Float

    data_position = Property(depends_on='_data_position')
    _data_position = Float

    update_position = Float

    min = Float(0)
    max = Float(100)
    steps = Int(137500)
    min_steps = Int(0)
    sign = Float
    units = Str('mm')

    linear_mapper = Instance(LinearMapper)

    home_delay = Float
    home_velocity = Float
    home_acceleration = Float
    homing_position = Int
    home_at_startup = Bool(True)
    home_position = CInt
    home_limit = CInt

    timer = None
    progress = None

    _not_moving_count = 0
    unique_id = Str

    def linear_mapper_factory(self):
        mi = self.min
        ma = self.max

        if self.sign == -1:
            mi, ma = ma, mi

        self.linear_mapper = LinearMapper(
            low_data=mi,
            high_data=ma,
            low_step=int(self.min_steps),
            high_step=int(self.steps))

    def block(self, n=3, tolerance=1, progress=None, homing=False):
        """
        """
        fail_cnt = 0
        pos_buffer = []

        while 1:
            if not self.is_simulation():
                break

            steps = self.load_data_position(set_pos=False)
            if steps is None:
                fail_cnt += 1
                if fail_cnt > 5:
                    break
                continue

            if homing:
                invoke_in_main_thread(self.trait_set, homing_position=steps)

            if progress is not None:
                progress.change_message('{} position = {}'.format(self.name, steps),
                                        auto_increment=False)

            pos_buffer.append(steps)
            if len(pos_buffer) == n:
                if abs(float(sum(pos_buffer)) / n - steps) < tolerance:
                    break
                else:
                    pos_buffer.pop(0)

            time.sleep(0.1)

        if fail_cnt > 5:
            self.warning('Problem Communicating')

    def load_data_position(self, set_pos=True):
        """
        """
        steps = self._read_motor_position(verbose=False)
        if steps is not None:
            pos = self.linear_mapper.map_data(steps)
            pos = max(self.min, min(self.max, pos))
            self.update_position = pos
            if set_pos:
                self._data_position = pos

            self.debug('Load data position {} {} steps= {}'.format(
                pos, self.units,
                steps))

        return steps

    def timer_factory(self):
        """
            reuse timer if possible
        """
        timer = self.timer

        func = self._update_position
        if timer is None:
            self._not_moving_count = 0
            timer = Timer(250, func)
        else:
            if timer.isActive():
                self.debug('reusing old timer')
            else:
                self._not_moving_count = 0
                timer = Timer(250, func)

        return timer

    # private
    def _read_motor_position(self, *args, **kw):
        pass

    def _load_config_attributes(self, config, args):
        for args in args:
            if len(args) == 3:
                section, key, cast = args
            else:
                cast = 'float'
                section, key = args

            self.set_attribute(config, key, section, key, cast=cast)

    # homing
    def _set_last_known_position(self, pos):
        self.debug('Set last known position: {}'.format(pos))
        hd = self._get_homing_persistence()
        if not hd:
            hd = {}

        hd['last_known_position'] = pos
        self._dump_homing_persistence(hd)

    def _get_last_known_position(self):
        hd = self._get_homing_persistence()
        if hd:
            return hd.get('last_known_position')

    @property
    def homing_path(self):
        return os.path.join(paths.hidden_dir, '{}-{}-homing.p'.format(self.name, self.unique_id))

    def _dump_homing_persistence(self, hd):
        p = self.homing_path
        with open(p, 'w') as wfile:
            pickle.dump(hd, wfile)

    def _get_homing_persistence(self):
        p = self.homing_path
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                return pickle.load(rfile)

    def _get_homing_required(self):
        hd = self._get_homing_persistence()
        if hd:
            return hd['homing_required']
# ============= EOF =============================================
