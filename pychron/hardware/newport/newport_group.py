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

# ============= enthought library imports =======================
from traits.api import Float, Tuple
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.axis import Axis

MAPPING = dict(acceleration='HA',
               deceleration='HD',
               # emergency_deceleration = 'HE',
               jerk='HJ',
               velocity='HV',
               axes='HN')


class NewportGroup(Axis):
    # acceleration = Float
    # deceleration = Float
    emergency_deceleration = None
    jerk = Float
    # velocity = Float
    name = 'GroupedAxes'
    machine_velocity = Float
    machine_acceleration = Float
    machine_deceleration = Float
    axes = Tuple

    #    calculate_parameters = Bool(True)
    id = None

    def _set_acceleration(self, v):
        self._acceleration = v

    def _set_deceleration(self, v):
        self._deceleration = v

    def _set_velocity(self, v):
        self._velocity = v

    def load(self, path):
        config = self.get_configuration(path)
        for attr in ['acceleration',
                     'deceleration',
                     # 'emergency_deceleration',
                     'jerk',
                     'velocity',
                     ]:
            self.set_attribute(config, attr, 'General', attr, cast='float')

        self.set_attribute(config, 'id', 'General', 'id', cast='int')
        self.axes = tuple(
                map(int, self.config_get(config, 'General', 'axes').split(',')))

        self.nominal_velocity = self.velocity
        self.nominal_acceleration = self.acceleration
        self.nominal_deceleration = self.deceleration

    def build_command(self, new_group):
        cmds = []
        for key, value in MAPPING.iteritems():
            if key is not 'axes':
                cmds.append(
                        '{}{}{:0.5f}'.format(self.id, value,
                                             getattr(self, key)))

        if new_group:
            gid = '{:n}HN{}'.format(self.id, ','.join(map(str, self.axes)))
            cmds = [gid] + cmds

        return ';'.join(cmds)

# ============= EOF ==============================================
