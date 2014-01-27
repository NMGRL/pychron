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
import datetime
import time

from traits.api import Property, String, Float, Any, Int, List
from traitsui.api import View, Item, VGroup

from pychron.core.helpers.timer import Timer
from pychron.loggable import Loggable

#============= standard library imports ========================
#============= local library imports  ==========================
FUDGE_COEFFS = (0, 0, 0)  # x**n+x**n-1....+c

class ExperimentStats(Loggable):
    elapsed = Property(depends_on='_elapsed')
    _elapsed = Float
    nruns = Int
    nruns_finished = Int
    etf = String
    time_at = String
    total_time = Property(depends_on='_total_time')
    _total_time = Float

    _timer = Any

    delay_between_analyses = Float
    delay_before_analyses = Float
    _start_time = None

#    experiment_queue = Any

    def calculate_duration(self, runs=None):
#        if runs is None:
#            runs = self.experiment_queue.cleaned_automated_runs
        dur = self._calculate_duration(runs)
        # add an empirical fudge factor
#         ff = polyval(FUDGE_COEFFS, len(runs))

        self._total_time = dur  # + ff
        return self._total_time

#    def calculate_etf(self):
#        runs = self.experiment_queue.cleaned_automated_runs
#        dur = self._calculate_duration(runs)
#        self._total_time = dur
#        self.etf = self.format_duration(dur)

    def format_duration(self, dur):
        dt = (datetime.datetime.now() + \
                       datetime.timedelta(seconds=int(dur)))
        return dt.strftime('%I:%M:%S %p %a %m/%d')

    def _calculate_duration(self, runs):
        dur = 0
        if runs:
            script_ctx = dict()
            warned = []
            ni = len(runs)
            dur = sum([a.get_estimated_duration(script_ctx, warned) for a in runs])

            btw = (self.delay_between_analyses * ni)
            dur += btw + self.delay_before_analyses

        return dur

    def _get_elapsed(self):
        return str(datetime.timedelta(seconds=self._elapsed))

    def _get_total_time(self):
        dur = datetime.timedelta(seconds=round(self._total_time))
        return str(dur)

    def traits_view(self):
        v = View(VGroup(
                        Item('nruns',
                            label='Total Runs',
                            style='readonly'
                            ),
                        Item('nruns_finished',
                             label='Completed',
                             style='readonly'
                             ),
                        Item('total_time',
                              style='readonly'),
                        Item('time_at', style='readonly'),
                        Item('etf', style='readonly', label='Est. finish'),
                        Item('elapsed',
                             style='readonly'),
                        )
                 )
        return v

    def start_timer(self):
        st = time.time()
        self._start_time = st
        def update_time():
            e = round(time.time() - st)
            self.trait_set(_elapsed=e)

        self._timer = Timer(1000, update_time)
        self._timer.start()

    def stop_timer(self):
        if self._timer:
            tt = self._total_time
            et = self._elapsed
            dt = tt - et
            self.info('Estimated total time= {:0.1f}, elapsed time= {:0.1f}, deviation= {:0.1f}'.format(tt, et, dt))
            self._timer.stop()

    def reset(self):
        self._start_time = None
        self.nruns_finished = 0
        self._elapsed = 0


class StatsGroup(ExperimentStats):
    experiment_queues = List
    def reset(self):
        ExperimentStats.reset(self)
        self.calculate()

    def calculate(self):
        """
            calculate the total duration
            calculate the estimated time of finish
        """
        #runs = [ai
        #        for ei in self.experiment_queues
        #            for ai in ei.cleaned_automated_runs]
        #
        #ni = len(runs)
        #self.nruns = ni
        # for ei in self.experiment_queues:
        #     dur=ei.stats.calculate_duration(ei.cleaned_automated_runs)
        #     if


        tt = sum([ei.stats.calculate_duration(ei.cleaned_automated_runs)
                 for ei in self.experiment_queues])
        self._total_time = tt
        offset = 0
        if self._start_time:
            offset = time.time() - self._start_time

        self.etf = self.format_duration(tt - offset)

    def calculate_at(self, sel):
        '''
            calculate the time at which a selected run will execute
        '''
        tt = 0
        for ei in self.experiment_queues:
            if sel in ei.cleaned_automated_runs:
                si = ei.cleaned_automated_runs.index(sel)
                tt += ei.stats.calculate_duration(ei.cleaned_automated_runs[:si + 1])
                break
            else:
                tt += ei.stats.calculate_duration()

        self.time_at = self.format_duration(tt)



#============= EOF =============================================
