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

# ============= standard library imports ========================

# ============= local library imports  ==========================


class DummyPM(object):
    patterns = ['PatternA', 'PatternB']
    def get_pattern_names(self):
        return self.patterns

    def execute_pattern(self, name):
        return name in self.patterns

    def stop_pattern(self):
        pass


class DummySM(object):
    pattern_manager = DummyPM()
    x = 1
    y = 2
    z = 3
    stage_map = '221-hole'
    hole = -1
    _temp_position = None
    def set_xy(self, *args, **kw):
        return True

    def linear_move_to(self, x, y):
        return 'OK'

    def moving(self, **kw):
        return True

    def stop(self):
        return True

    def define_home(self, *args, **kw):
        return True

    def do_jog(self, name):
        pass

    def get_uncalibrated_xy(self):
        return 0, 0

    def get_z(self):
        return 1.0

    def linear_move(self, x, y, *args, **kw):
        pass

    def single_axis_move(self, *args, **kw):
        pass

    def _set_stage_map(self, *args, **kw):
        pass

    def _set_hole(self, *args, **kw):
        pass


class DummyLM(object):
    stage_manager = DummySM()
    zoom = 30
    beam = 1.5
    record_lasing_video = False
    def set_beam_diameter(self, d, **kw):
        return True

    def set_laser_power(self, *args, **kw):
        pass

    def enable_laser(self):
        return True

    def disable_laser(self):
        return True

    def get_laser_watts(self):
        return 14.0

    def start_recording(self, *args, **kw):
        pass
    def stop_recording(self, *args, **kw):
        pass

    def start_power_recording(self):
        pass
    def stop_power_recording(self):
        pass

class DummyDevice(object):
    def get(self, *args, **kw):
        return 0.1

    def set(self, v):
        return 'OK'

alphas = [chr(i) for i in range(65, 65 + 26, 1)]


class DummyELM(object):
    def open_valve(self, v):
        if len(v) == 1 and v in alphas:
            return True

    def close_valve(self, v):
        if len(v) == 1:
            return True

    def get_valve_state(self, v):
        return True

    def get_valve_states(self):
        return ','.join(map(str, [True, True, False]))

    def get_manual_state(self, v):
        return True

    def get_device(self, n):

        _d = DummyDevice()
        d = None
        return d

    def get_software_lock(self, n):
        return False
# ============= EOF =====================================
