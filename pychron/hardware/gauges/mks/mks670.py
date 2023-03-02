# ===============================================================================
# Copyright 2023 ross
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
from pychron.hardware import get_float
from pychron.hardware.core.core_device import CoreDevice


class MKS670(CoreDevice):

    def initialize(self):
        # set to pressure mode
        msg = self.make_global_message('01', '00')
        resp = self.ask(msg)

        return True

    @get_float(default=0)
    def get_pressure(self, channel=0):
        msg = self.make_global_message('00', f'{channel:02n}')
        resp = self.ask(msg)

        msg = self.make_global_message('02', '0?')
        resp = self.ask(msg)
        if resp:
            torr = resp.split(' ')[1].strip()
            return torr

    def make_global_message(self, parameter, data):
        return f'@{parameter}{data}\n'

# ============= EOF =============================================
