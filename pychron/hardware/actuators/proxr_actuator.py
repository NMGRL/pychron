# ===============================================================================
# Copyright 2020 ross
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
from pychron.hardware.ncd.relay import ProXR


class ProXRActuator(ProXR, GPActuator):
    def _actuate(self, obj, action):
        addr = get_switch_address(obj)
        if action.lower() == "open":
            self.open_channel(addr)
        else:
            self.close_channel(addr)
        return True

    def get_channel_state(self, obj, **kw):
        return ProXR.get_channel_state(self, get_switch_address(obj), **kw)


# ============= EOF =============================================
