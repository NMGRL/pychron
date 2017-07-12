# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================
import time
from datetime import datetime, timedelta

from traits.api import Property, String, Float, Any, Int, List, Instance, Bool

from pychron.core.helpers.timer import Timer
from pychron.core.ui.pie_clock import PieClockModel
from pychron.experiment.duration_tracker import AutomatedRunDurationTracker
from pychron.loggable import Loggable
from pychron.pychron_constants import MEASUREMENT_COLOR, EXTRACTION_COLOR, NULL_STR


class ExperimentStats(Loggable):
    elapsed = Property(depends_on='_elapsed')
    _elapsed = Float

    run_elapsed = Property(depends_on='_run_elapsed')
    _run_elapsed = Float

    remaining = Property(depends_on='_elapsed, _total_time')

    nruns = Int
    nruns_finished = Int
    etf = String
    start_at = String
    end_at = String
    run_duration = String
    current_run_duration = String
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
    _run_start = 0

    # experiment_queue = Any

    def calculate_duration(self, runs=None):
        self.duration_tracker.load()
        dur = self._calculate_duration(runs)
        self._total_time = dur
        return self._total_time

    def format_duration(self, dur, post=None, fmt='%H:%M:%S %a %m/%d'):
        if post is None:
            post = self._post
            if not post:
                post = datetime.now()

        dt = post + timedelta(seconds=int(dur))
        if fmt == 'iso':
            return dt.isoformat()
        else:
            return dt.strftime(fmt)

    def start_timer(self):
        st = time.time()
        self._post = datetime.now()

        def update_time():
            e = round(time.time() - st)
            d = {'_elapsed': e}
            if self._run_start:
                re = round(time.time() - self._run_start)
                d['_run_elapsed'] = re
            self.trait_set(**d)

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
        self._run_elapsed = 0
        self._run_start = 0

    def update_run_duration(self, run, t):
        a = self.duration_tracker
        a.update(run, t)

    def start_run(self, run):
        self._run_start = time.time()
        self.setup_run_clock(run)

        self.current_run_duration = self.get_run_duration(run.spec, as_str=True)

    def get_run_duration(self, run, as_str=False):
        sh = run.script_hash
        if sh in self.duration_tracker:
            self.debug('using duration tracker value')
            rd = self.duration_tracker[sh]
        else:
            rd = run.get_estimated_duration(force=True)
        rd = round(rd)
        if as_str:
            rd = str(timedelta(seconds=rd))

        self.debug('run duration: {}'.format(rd))
        return rd

    def finish_run(self):
        self._run_start = 0
        self.nruns_finished += 1
        self.debug('finish run. runs completed={}'.format(self.nruns_finished))
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

    # private
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
                    t = a.make_truncated_script_hash()
                    if a.has_conditionals() and t in self.duration_tracker:
                        run_dur += self.duration_tracker.probability_model(sh, t)
                    else:
                        run_dur += self.duration_tracker[sh]
                else:
                    run_dur += a.get_estimated_duration(script_ctx, warned, True)

            btw = self.delay_between_analyses * (ni - 1)
            dur = run_dur + btw + self.delay_before_analyses
            self.debug('nruns={} before={}, run_dur={}, btw={}'.format(ni, self.delay_before_analyses,
                                                                       run_dur, btw))

        return dur

    def _get_run_elapsed(self):
        return str(timedelta(seconds=self._run_elapsed))

    def _get_elapsed(self):
        return str(timedelta(seconds=self._elapsed))

    def _get_total_time(self):
        dur = timedelta(seconds=round(self._total_time))
        return str(dur)

    def _get_remaining(self):
        if not self._total_time:
            dur = NULL_STR
        else:
            # self.debug('Remaining seconds={}, tt={}, e={}'.format(self._total_time-self._elapsed, self._total_time, self._elapsed))
            dur = timedelta(seconds=round(self._total_time - self._elapsed))
        return str(dur)


class StatsGroup(ExperimentStats):
    experiment_queues = List

    # @caller
    def reset(self):
        # print 'resetwas'
        self.calculate(force=True)
        ExperimentStats.reset(self)

    def calculate(self, force=False):
        """
            calculate the total duration
            calculate the estimated time of finish
        """
        # runs = [ai
        # for ei in self.experiment_queues
        #            for ai in ei.cleaned_automated_runs]
        #
        # ni = len(runs)
        # self.nruns = ni
        # for ei in self.experiment_queues:
        #     dur=ei.stats.calculate_duration(ei.cleaned_automated_runs)
        #     if
        if force or not self._total_time:
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

    def recalculate_etf(self):
        tt = sum([ei.stats.calculate_duration(ei.cleaned_automated_runs)
                  for ei in self.experiment_queues])

        self._total_time = tt + self._elapsed
        self.etf = self.format_duration(tt, post=datetime.now())

    def calculate_at(self, sel, at_times=True):
        """
            calculate the time at which a selected run will execute
        """
        self.debug('calculating time of run {}'.format(sel.runid))
        et = 0
        st = 0
        for ei in self.experiment_queues:
            if sel in ei.cleaned_automated_runs:

                si = ei.cleaned_automated_runs.index(sel)

                st += ei.stats.calculate_duration(
                    ei.executed_runs + ei.cleaned_automated_runs[:si]) + ei.delay_between_analyses
                # et += ei.stats.calculate_duration(ei.executed_runs+ei.cleaned_automated_runs[:si + 1])

                rd = self.get_run_duration(sel)
                et = st + rd

                rd = timedelta(seconds=round(rd))
                self.run_duration = str(rd)

                break
            else:
                et += ei.stats.calculate_duration()

        if at_times:
            # self.time_at = self.format_duration(tt)
            self.end_at = self.format_duration(et)
            if st:
                self.start_at = self.format_duration(st)

    @property
    def etf_iso(self):
        return self.format_duration(self._total_time, fmt='iso')

# ============= EOF =============================================
