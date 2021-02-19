# ===============================================================================
# Copyright 2021 ross
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

from traitsui.api import View, UItem, ButtonEditor
from pychron.hardware.pyrometer import Pyrometer


def checksum(t):
    c = 0
    for i in range(0, len(t), 2):
        tt = t[i:i + 2]
        c ^= int(tt, 16)
    return '{:02X}'.format(c)


class MicroEpsilonPyrometer(Pyrometer):
    def read_temperature(self):
        cmd = '01'
        resp = self.ask(cmd, is_hex=True)
        t = (int(resp, 16)-1000)/10
        t = float(t)
        return t

    def set_laser_pointer(self, onoff):
        cmd = 'A5'
        data = int(onoff)
        pc = '{}{:02X}'.format(cmd, data)
        chk = checksum(pc)

        c = '{}{}'.format(pc, chk)
        self.ask(c, is_hex=True)

    def traits_view(self):
        v = View(UItem('pointer', editor=ButtonEditor(label_value='pointer_label')),)
        return v


if __name__ == '__main__':
    m = MicroEpsilonPyrometer()
    m.set_laser_pointer(True)
    m.set_laser_pointer(False)
    # print(checksum('A37003D4'))
    # print(checksum('A3711770'))
# ============= EOF =============================================
