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

#============= enthought library imports =======================
from traits.api import Float, Str
from traitsui.api import View, Item, VGroup, EnumEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pyscripts.commands.core import Command
from traitsui.menu import OKCancelButtons

class Ramp(Command):
    setpoint = Float(1)
    rate = Float(1)
    start = Str
    _default_period = 60
    period = Float(_default_period)

    def traits_view(self):
        v = View(Item('setpoint', label='Setpoint (C)'),
               Item('rate', label='Rate C/hr'),
               VGroup(
                      Item('start', label='Start Setpoint (C)'),
                      Item('period', label='Update Period (s)'),
                      show_border=True,
                      label='Optional'
                      ),
                buttons=OKCancelButtons
                )
        return v

    def _to_string(self):
        start = None
        try:
            start = float(start)
        except (ValueError, TypeError):
            pass


        words = [('setpoint', self.setpoint, True),
                 ('rate', self.rate, True),
               ]
        if start is not None:
            words.append(('start', start, True))

        if self.period != self._default_period:
            words.append(('period', self.period, True))

        return self._keywords(words)


time_dict = dict(h='hours', m='minutes', s='seconds')
class Setpoint(Command):
    setpoint = Float
    duration = Float
    units = Str('h')

    def _get_view(self):
        v = VGroup(Item('setpoint', label='Temperature (C)'),
                   Item('duration', label='Duration (units)'),
                   Item('units', editor=EnumEditor(values=time_dict),

                    ),
               )

        return v
    def _to_string(self):
        words = [('temperature', self.setpoint, True),
               ('duration', self.duration, True),
               ('units', self.units)
               ]
        return self._keywords(words)


# ============= EOF =============================================
