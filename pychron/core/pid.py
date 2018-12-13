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
from __future__ import absolute_import
from traits.api import HasTraits, Range, Float
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================
from pychron.paths import paths

ATTRS = ('kp', 'ki', 'kd', 'kdt')


class PID(HasTraits):

    kp = Range(0.0, 10.0, 1.25)
    ki = Range(0.0, 2.0, 0.25)
    kd = Range(0.0, 2.0, 0.25)
    kdt = Float(0.5)
    max_output = Float
    min_output = Float

    def __init__(self, kp=0.25, ki=0, kd=0, dt=1, min_output=0, max_output=100):
        self.max_output = max_output
        self.min_output = min_output
        self.kd = kd
        self.ki = ki
        self.kp = kp
        self.kdt = dt

        self._integral_err = 0
        self._prev_err = 0

    def load_from_obj(self, jd):
        for a in ATTRS:
            setattr(self, a, jd.get(a))

    def get_dump_obj(self):
        obj = {a: getattr(self, a) for a in ATTRS}
        return obj

    def load(self):
        p = self.persistence_path
        with open(p, 'rb') as rfile:
            jd = yaml.load(rfile)
            self.load_from_obj(jd)

    def dump(self):
        p = self.persistence_path
        with open(p, 'wb') as wfile:
            obj = self.get_dump_obj()
            yaml.dump(obj, wfile)

    @property
    def persistence_path(self):
        return os.path.join(paths.setup_dir, 'pid.yaml')

    def reset(self):
        self._integral_err = 0
        self._prev_err = 0

    def get_value(self, error):
        dt = self.kdt
        self._integral_err += (error * dt)
        derivative = (error - self._prev_err) / dt
        output = (self.kp * error) + (self.ki * self._integral_err) + (self.kd * derivative)
        self._prev_err = error
        return min(self.max_output, max(self.min_output, output))

    def traits_view(self):
        v = View(VGroup(VGroup(Item('kp', label='P'),
                        Item('ki', label='I'),
                        Item('kd', label='D'),
                        Item('kdt', label='Dt')),
                        HGroup(Item('min_output'),
                               Item('max_output'))),
                 title='Edit PID',
                 buttons=['OK','Cancel'])
        return v
# ============= EOF =============================================
