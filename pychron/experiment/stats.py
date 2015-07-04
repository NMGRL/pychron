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
from traits.api import Property, String, Float, Any, Int, List, Instance, Bool
from traitsui.api import View, Item, VGroup, UItem
# ============= standard library imports ========================
from datetime import datetime, timedelta
import os
import time
# ============= local library imports  ==========================
from pychron.core.helpers.timer import Timer
from pychron.core.ui.pie_clock import PieClockModel
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import MEASUREMENT_COLOR, EXTRACTION_COLOR

FUDGE_COEFFS = (0, 0, 0)  # x**n+x**n-1....+c


class AutomatedRunDurationTracker(Loggable):
    items = List

    def load(self):
        items = []
        if os.path.isfile(paths.duration_tracker):
            with open(paths.duration_tracker, 'r') as rfile:
                for line in rfile:
                    line = line.strip()
                    if line:
                        h, d = line.split(',')
                        items.append((h, float(d)))
        self.items = items

    def update(self, rh, t):

        p = paths.duration_tracker

        out = []
        exists = False
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                for line in rfile:
                    line = line.strip()
                    if line:
                        h, d = line.split(',')

                        # update the runs duration by taking average of current (t) and previous (d) durations
                        if h == rh:
                            o = (h, (float(d) + t) * 0.5)
                            exists = True
                        else:
                            o = (h, d)
                        out.append(o)
        if not exists:
            out.append((rh, t))

        with open(p, 'w') as wfile:
            for line in out:
                wfile.write('{},{}\n'.format(*line))

    def __contains__(self, v):
        return next((True for h, d in self.items if h == v), False)

    def __getitem__(self, item):
        return next((d for h, d in self.items if h == item), 0)


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
    # _start_time = None
    _post = None

    use_clock = Bool(False)
    clock = Instance(PieClockModel, ())
    duration_tracker = Instance(AutomatedRunDurationTracker, ())

    #    experiment_queue = Any

    def calculate_duration(self, runs=None):
        #        if runs is None:
        #            runs = self.experiment_queue.cleaned_automated_runs
        self.duration_tracker.load()
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
        post = self._post
        if not post:
            post = datetime.now()

        dt = post + timedelta(seconds=int(dur))
        return dt.strftime('%I:%M:%S %p %a %m/%d')

    def _calculate_duration(self, runs):

        dur = 0
        if runs:
            script_ctx = dict()
            warned = []
            ni = len(runs)

            run_dur = 0
            for a in runs:
                sh = a.script_hash
                if sh in self.duration_tracker:
                    run_dur += self.duration_tracker[sh]
                else:
                    run_dur += a.get_estimated_duration(script_ctx, warned, True)

            # run_dur = sum([a.get_estimated_duration(script_ctx, warned, True) for a in runs])

            btw = self.delay_between_analyses * (ni - 1)
            dur = run_dur + btw + self.delay_before_analyses
            self.debug('before={}, run_dur={}, btw={}'.format(self.delay_before_analyses,
                                                              run_dur, btw))

        return dur

    def _get_elapsed(self):
        return str(timedelta(seconds=self._elapsed))

    def _get_total_time(self):
        dur = timedelta(seconds=round(self._total_time))
        return str(dur)

    def traits_view(self):
        v = View(VGroup(
            Item('nruns',
                 label='Total Runs',
                 style='readonly'),
            Item('nruns_finished',
                 label='Completed',
                 style='readonly'),
            Item('total_time',
                 style='readonly'),
            Item('time_at', style='readonly'),
            Item('etf', style='readonly', label='Est. finish'),
            Item('elapsed',
                 style='readonly')),
            UItem('clock', style='custom', width=100, height=100, defined_when='use_clock'))
        return v

    def start_timer(self):
        st = time.time()
        self._post = datetime.now()
        # self._start_time = st

        def update_time():
            e = round(time.time() - st)
            self.trait_set(_elapsed=e)

        self._timer = Timer(1000, update_time)
        self._timer.start()

    def stop_timer(self):
        self.debug('Stop timer. self._timer: {}'.format(self._timer))
        if self._timer:
            tt = self._total_time
            et = self._elapsed
            dt = tt - et
            self.info('Estimated total time= {:0.1f}, elapsed time= {:0.1f}, deviation= {:0.1f}'.format(tt, et, dt))
            self._timer.stop()

    def reset(self):
        # self._start_time = None
        self._post = None
        self.nruns_finished = 0
        self._elapsed = 0

    def update_run_duration(self, run, t):
        a = self.duration_tracker
        a.update(run.spec.script_hash, t)

    def finish_run(self):

        self.nruns_finished += 1
        if self.clock:
            self.clock.stop()

    def continue_run(self):
        if self.clock:
            self.clock.finish_slice()

    def setup_run_clock(self, run):
        if self.use_clock:
            ctx = run.spec.make_script_context()
            extraction_slice = run.extraction_script.calculate_estimated_duration(ctx)
            measurement_slice = run.measurement_script.calculate_estimated_duration(ctx)

            def convert_hexcolor_to_int(c):
                c = c[1:]
                func = lambda i: int(c[i:i + 2], 16)
                return map(func, (0, 2, 4))

            ec, mc = map(convert_hexcolor_to_int,
                         (EXTRACTION_COLOR, MEASUREMENT_COLOR))

            self.clock.set_slices([extraction_slice, measurement_slice],
                                  [ec, mc])
            self.clock.start()


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
        # runs = [ai
        #        for ei in self.experiment_queues
        #            for ai in ei.cleaned_automated_runs]
        #
        # ni = len(runs)
        # self.nruns = ni
        # for ei in self.experiment_queues:
        #     dur=ei.stats.calculate_duration(ei.cleaned_automated_runs)
        #     if
        self.debug('calculating experiment stats')
        tt = sum([ei.stats.calculate_duration(ei.cleaned_automated_runs)
                  for ei in self.experiment_queues])

        self.debug('total_time={}'.format(tt))
        self._total_time = tt
        # offset = 0
        # if self._start_time:
        #     offset = time.time() - self._start_time

        # self.etf = self.format_duration(tt - offset)
        self.etf = self.format_duration(tt)

    def calculate_at(self, sel):
        """
            calculate the time at which a selected run will execute
        """
        self.debug('calculating time of run {}'.format(sel.runid))
        tt = 0
        for ei in self.experiment_queues:
            if sel in ei.cleaned_automated_runs:
                si = ei.cleaned_automated_runs.index(sel)
                tt += ei.stats.calculate_duration(ei.cleaned_automated_runs[:si + 1])
                break
            else:
                tt += ei.stats.calculate_duration()

        self.time_at = self.format_duration(tt)

# ============= EOF =============================================
