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

from traits.api import Float, Bool

from pychron.core.helpers.strtools import csv_to_floats
from pychron.lasers.stage_managers.stage_manager import StageManager


class RemoteStageManager(StageManager):
    xmin = Float
    xmax = Float

    ymin = Float
    ymax = Float

    zmin = Float
    zmax = Float

    use_sign_position_correction = Bool(False)
    y_sign = 1
    x_sign = 1
    z_sign = 1

    def load(self):
        config = self.get_configuration()
        for a in ('x', 'y', 'z'):
            low, high = csv_to_floats(config.get('Axes Limits', a))
            setattr(self, '{}min'.format(a), low)
            setattr(self, '{}max'.format(a), high)

            v = config.get('Signs', a)
            setattr(self, '{}_sign'.format(a), int(v))

        self.set_attribute(config, 'use_sign_position_correction', 'Signs', 'use_sign_position_correction',
                           cast='boolean')

        return super(RemoteStageManager, self).load()

    def get_current_position(self):
        self.parent.update_position()
        self.debug('get_current_position {},{}'.format(self.parent.x, self.parent.y))
        return self.parent.x, self.parent.y

# ============= EOF =============================================
