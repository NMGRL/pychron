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
from pychron.hardware.actuators import get_switch_address
from pychron.hardware.actuators.gp_actuator import GPActuator
from pychron.hardware.labjack.base_u3_lv import BaseU3LV


class U3Actuator(BaseU3LV, GPActuator):
    def _actuate(self, obj, action):
        return BaseU3LV.set_channel_state(
            self, get_switch_address(obj), action.lower() == "open"
        )

    def get_channel_state(self, obj, **kw):
        return BaseU3LV.get_channel_state(self, get_switch_address(obj), **kw)


# ============= EOF =============================================
