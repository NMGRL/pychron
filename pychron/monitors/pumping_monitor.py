#===============================================================================
# Copyright 2011 Jake Ross
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
# from traits.api import HasTraits
# from traitsui.api import View,Item,Group,HGroup,VGroup

#============= standard library imports ========================
import time
from monitor import Monitor
# from threading import Thread
#============= local library imports  ==========================

cnt = 0
class PumpingMonitor(Monitor):
    '''
        G{classtree}
    '''
    gauge_manager = None
    tank_gauge_name = 'gauge1'
    pump_gauge_name = 'gauge2'
    # pumping_duration=Float
    # idle_duration=Float
    name = 'AnalyticalPumpingMonitor'


    def _monitor_(self):
        '''
        '''
        pump_start = 0
        idle_start = 0

        def get_time(_start_):
            ct = time.time()
            _dur_ = 0
            if _start_ == 0:
                _start_ = ct
            else:
                _dur_ = ct - _start_
            return _start_, _dur_

        while self.gauge_manager is not None:
            state = self._get_pumping_state()

            if state == 'pumping':
                idle_start = 0
                pump_start, pump_duration = get_time(pump_start)
                self.parent.update_pumping_duration(self.name, pump_duration)
            else:  # state=='idle'
                pump_start = 0
                idle_start, idle_duration = get_time(idle_start)
                # print 'idle duir',idle_duration
                self.parent.update_idle_duration(self.name, idle_duration)

            time.sleep(1)
    def _get_pumping_state(self):
        '''
        '''
        state = 'idle'
        # gm=self.gauge_manager
        global cnt

        if cnt >= 5 and cnt < 10:
            state = 'pumping'

#        tankgauge=gm.get_gauge_by_name(self.tank_gauge_name)
#        if tankgauge.pressure<1:
#            state='pumping'

        cnt += 1
        return state
#============= EOF ====================================
