#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Str

#============= standard library imports ========================
from datetime import datetime
#============= local library imports  ==========================


class Alarm(HasTraits):
    alarm_str = Str
    triggered = False

    def get_alarm_params(self):
        als = self.alarm_str
        cond = als[0]
        if cond not in ['<', '>']:
            cond = '='
            trigger = float(als)
        else:
            trigger = float(als[1:])
        return cond, trigger

    def test_condition(self, value):
        cond, trigger = self.get_alarm_params()

        expr = 'value {} {}'.format(cond, trigger)

        triggered = eval(expr, {}, dict(value=value))

        if triggered:
            if not self.triggered:
                self.triggered = True
        else:
            self.triggered = False

        return self.triggered

    def get_message(self, value):
        cond, trigger = self.get_alarm_params()
        tstamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')

        return '<<<<<<ALARM {}>>>>>> {} {} {}'.format(tstamp, value, cond, trigger)
#============= EOF =============================================
