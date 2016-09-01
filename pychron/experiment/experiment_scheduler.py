# ===============================================================================
# Copyright 2016 ross
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

import datetime
import time

from traits.api import Bool, Time, Date
from traitsui.api import View, UItem, HGroup

from pychron.loggable import Loggable


class ExperimentScheduler(Loggable):
    delayed_start_enabled = Bool
    start_time = Time
    start_date = Date

    _min_start_datetime = None

    def setup(self):
        self._min_start_datetime = n = datetime.datetime.now()
        self.start_time = n.time()
        self.start_date = n.date()

    def traits_view(self):
        v = View(HGroup(UItem('delayed_start_enabled'),
                        UItem('start_date', enabled_when='delayed_start_enabled'),
                        UItem('start_time', enabled_when='delayed_start_enabled'),
                        show_border=True),
                 title='Configure Scheduler',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v

    def start_datetime(self):
        if self.start_date and self.start_time:
            return datetime.datetime.combine(self.start_date, self.start_time)

    def get_startf(self):
        dt = self.start_datetime()
        if dt:
            return time.mktime(dt.timetuple())


if __name__ == '__main__':
    e = ExperimentScheduler()
    e.setup()
    e.configure_traits()
# ============= EOF =============================================
