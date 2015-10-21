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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.base_linear_drive import BaseLinearDrive
from pychron.hardware.core.core_device import CoreDevice


class MDriveMotor(CoreDevice, BaseLinearDrive):
    def load_additional_args(self, config):
        args = [
            ('Motion', 'steps', 'int'),
            ('Motion', 'min_steps', 'int'),
            ('Motion', 'sign'),
            ('Motion', 'velocity'),
            ('Motion', 'acceleration'),

            ('Homing', 'home_delay'),
            ('Homing', 'home_velocity'),
            ('Homing', 'home_acceleration'),
            ('Homing', 'home_at_startup', 'boolean'),
            ('Homing', 'home_position'),
            ('Homing', 'home_limit'),

            ('General', 'min'),
            ('General', 'max'),
            ('General', 'nominal_position'),
            ('General', 'units')]
        self._load_config_attributes(args)

        self.linear_mapper_factory()

    def is_simulation(self):
        return self.simulation

    # private
    def _read_motor_position(self, *args, **kw):
        pass
# ============= EOF =============================================



