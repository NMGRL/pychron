# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, Button, Str
from traitsui.api import View, Item

from pychron.hardware.kerr.kerr_motor import KerrMotor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable

class KerrManager(Loggable):

    motor = Instance(KerrMotor)
    read_status = Button
    result = Str
    def _read_status_fired(self):
        motor = self.motor


        controlbyte = '00111111'
        cb = list(controlbyte)
        cb.reverse()

        result = motor.read_status(controlbyte)[2:-2]
        print result, len(result)
        pi = 0
        for (n, l), controlbit in zip([('posbyte', 4), ('cursence', 1), ('velocity', 2),
                                       ('aux', 1), ('homepos', 4), ('devicetype', 2),
                                       # ('poserr', 2), ('pathpoints', 1)
                                       ], cb):

            if not int(controlbit):
                continue
            l *= 2
            print n, result[pi:pi + l]
            pi = pi + l

#        sb = result[2:]
#
#        ba = make_bitarray(int(sb, 16))
#
#        try:
#            n = 8
#            bh = ' '.join([str(n - i) for i in range(n)])
#            ba = ' '.join([str(bi) for bi in ba])
#            self.result = '{}\n{}\n{}'.format(str(result), bh, ba)
#        except Exception, e:
#            import traceback
#            traceback.print_tb()
#            self.result = str(e)

    def traits_view(self):
        v = View(Item('read_status', show_label=False),
                 Item('result', show_label=False, style='custom'),
                 width=500,
                 height=300,
                 resizable=True
                 )
        return v
# ============= EOF =============================================
