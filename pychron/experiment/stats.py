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

from traits.api import Property, String, Float, Any, Int, List, Instance

from pychron.core.helpers.timer import Timer
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.experiment.duration_tracker import AutomatedRunDurationTracker
from pychron.loggable import Loggable
from pychron.pychron_constants import NULL_STR


class ExperimentStats(Loggable):
    delay_between_analyses = Float
    delay_before_analyses = Float
    delay_after_blank = Float
    delay_after_air = Float

    duration_tracker = Instance(AutomatedRunDurationTracker, ())
    _duration_tracker_loaded = False
    _dirty = True

    def update_run_duration(self, run, t):
        a = self.duration_tracker
        a.update(run, t)
        self._dirty = True

    def invalidate(self):
        self._dirty = True

    def load_duration_tracker(self):
        if not self._duration_tracker_loaded:
            self.duration_tracker.load()
            self._duration_tracker_loaded = True

    def calculate_duration(self, runs=None):
        self.load_duration_tracker()
        dur = self._calculate_duration(runs)
        return dur

        # self._total_time = dur
        # return self._total_time

    def get_run_duration(self, run, as_str=False):
        sh = run.script_hash
        if sh in self.duration_tracker:
            self.debug("using duration tracker value")
            rd = self.duration_tracker[sh]
        else:
            rd = run.get_estimated_duration(force=True)
        rd = round(rd)
        if as_str:
            rd = str(timedelta(seconds=rd))

        self.debug("run duration: {}".format(rd))
        return rd

    # private
    def _calculate_duration(self, runs):
        dur = 0
        if runs:
            script_ctx = dict()
            warned = []
            ni = len(runs)

            btw = 0
            run_dur = 0
            d = 0
            for a in runs:
                sh = a.script_hash

                if sh in self.duration_tracker:
                    run_dur += self.duration_tracker[sh]
                else:
                    run_dur += a.get_estimated_duration(script_ctx, warned, True)
                d = a.get_delay_after(
                    self.delay_between_analyses,
                    self.delay_after_blank,
                    self.delay_after_air,
                )
                btw += d

            # subtract the last delay_after because experiment doesn't delay after last analysis
            btw -= d

            dur = run_dur + self.delay_before_analyses + btw
            self.debug(
                "nruns={} before={}, run_dur={}, btw={}".format(
                    ni, self.delay_before_analyses, run_dur, btw
                )
            )

        return dur


class StatsGroup(Loggable):
    experiment_queues = List
    active_queue = Any

    nruns = Int
    etf = String
    start_at = String
    end_at = String

    nruns_finished = Int
    run_duration = String
    current_run_duration = String
    current_run_duration_f = Float

    _timer = Any

    elapsed = Property(depends_on="_elapsed")
    _elapsed = Float

    run_elapsed = Property(depends_on="_run_elapsed")
    _run_elapsed = Float

    total_time = Property(depends_on="_total_time")
    _total_time = Float

    remaining = Property(depends_on="_elapsed, _total_time")

    _post = None
    _run_start = 0
    _queue_sig = None

    # not used
    def continue_run(self):
        pass

    # ========= Active Queue ============
    def calculate_duration(self, *args, **kw):
        queue = self.active_queue
        if queue is None:
            queue = self.experiment_queues[0]
        if queue:
            return queue.stats.calculate_duration(*args, **kw)

    def get_run_duration(self, *args, **kw):
        queue = self.active_queue
        if queue is None:
            queue = self.experiment_queues[0]
        if queue:
            return queue.stats.get_run_duration(*args, **kw)

    def update_run_duration(self, *args, **kw):
        queue = self.active_queue
        if queue is None:
            queue = self.experiment_queues[0]

        if queue:
            queue.stats.update_run_duration(*args, **kw)

    # ====================================

    def start_timer(self) -> None:
        st = time.time()
        self._post = datetime.now()

        def update_time() -> None:
            e = round(time.time() - st)
            d = {"_elapsed": e}
            if self._run_start:
                re = round(time.time() - self._run_start)
                d["_run_elapsed"] = re
            invoke_in_main_thread(self.trait_set, **d)

        self._timer = Timer(900, update_time)

    def stop_timer(self) -> None:
        self.debug("Stop timer. self._timer: {}".format(self._timer))
        if self._timer:
            tt = self._total_time
            et = self._elapsed
            dt = tt - et
            self.info(
                "Estimated total time= {:0.1f}, elapsed time= {:0.1f}, deviation= {:0.1f}".format(
                    tt, et, dt
                )
            )
            self._timer.stop()

    def reset(self):
        self.calculate(force=True)

        self._post = None
        self._elapsed = 0
        self._run_elapsed = 0
        self.nruns_finished = 0
        self._run_start = 0

    def start_run(self, run):
        self._run_start = time.time()
        self.current_run_duration = self.active_queue.stats.get_run_duration(
            run.spec, as_str=True
        )
        self.current_run_duration_f = self.active_queue.stats.get_run_duration(run.spec)

    def finish_run(self):
        self._run_start = 0
        self.nruns_finished += 1
        self.debug("finish run. runs completed={}".format(self.nruns_finished))

    def _calculate_total_duration(self):
        """Calculate total duration across all experiment queues."""
        return sum(
            [
                ei.stats.calculate_duration(ei.cleaned_automated_runs)
                for ei in self.experiment_queues
            ]
        )

    def _clear_dirty_flags(self):
        """Clear dirty flags on all experiment queue stats."""
        for ei in self.experiment_queues:
            ei.stats._dirty = False

    def calculate(self, force=False) -> None:
        """
        calculate the total duration
        calculate the estimated time of finish
        """
        queue_sig = self._make_queue_sig()
        should_recalculate = (
            force
            or not self._total_time
            or queue_sig != self._queue_sig
            or any(ei.stats._dirty for ei in self.experiment_queues)
        )
        if should_recalculate:
            nruns = sum(
                [len(ei.cleaned_automated_runs) for ei in self.experiment_queues]
            )

            self.debug("calculating experiment stats")
            tt = self._calculate_total_duration()
            self._clear_dirty_flags()
            self.debug("total_time={}".format(tt))

            # Set nruns first to ensure UI updates, then set the other stats
            self.trait_set(
                nruns=nruns,
                _total_time=tt,
                etf=self.format_duration(tt),
                _queue_sig=queue_sig,
            )

    def recalculate_etf(self):
        """Recalculate estimated time to finish based on current elapsed time."""
        tt = self._calculate_total_duration()
        self._clear_dirty_flags()

        self.trait_set(
            _total_time=tt + self._elapsed,
            etf=self.format_duration(tt, post=datetime.now()),
            _queue_sig=self._make_queue_sig(),
        )

    def refresh_on_queue_change(self):
        if self.experiment_queues:
            self.calculate(force=True)

    def calculate_at(self, sel, at_times=True):
        """
        calculate the time at which a selected run will execute
        """
        self.debug("calculating time of run {}".format(sel.runid))
        st, et = self._calculate_at(sel)

        if at_times:
            self.end_at = self.format_duration(et)
            if st:
                self.start_at = self.format_duration(st)

    def get_endtime(self, sel):
        st, et = self._calculate_at(sel)
        return et

    def get_starttime(self, sel):
        st, et = self._calculate_at(sel)
        return st

    def format_duration(self, dur, post=None, fmt="%H:%M:%S %a %m/%d"):
        if post is None:
            post = self._post
            if not post:
                post = datetime.now()

        dt = post + timedelta(seconds=int(dur))
        if fmt == "iso":
            return dt.isoformat()
        else:
            return dt.strftime(fmt)

    @property
    def etf_iso(self):
        return self.format_duration(self._total_time, fmt="iso")

    def _calculate_at(self, sel):
        et = 0
        st = 0
        for ei in self.experiment_queues:
            stats = ei.stats
            if sel in ei.cleaned_automated_runs:
                si = ei.cleaned_automated_runs.index(sel)

                st += (
                    stats.calculate_duration(
                        ei.executed_runs + ei.cleaned_automated_runs[:si]
                    )
                    + ei.delay_between_analyses
                )

                rd = stats.get_run_duration(sel)
                et = st + rd

                rd = timedelta(seconds=round(rd))
                self.run_duration = str(rd)
                break
            else:
                et += stats.calculate_duration()
        return st, et

    def _make_queue_sig(self):
        sig = []
        for queue in self.experiment_queues:
            runs = tuple(
                (
                    ri.runid,
                    ri.state,
                    ri.skip,
                    ri.executable,
                    getattr(ri, "_changed", False),
                )
                for ri in queue.automated_runs
            )
            sig.append(
                (
                    id(queue),
                    queue.delay_before_analyses,
                    queue.delay_between_analyses,
                    queue.delay_after_blank,
                    queue.delay_after_air,
                    len(queue.cleaned_automated_runs),
                    runs,
                )
            )
        return tuple(sig)

    def _get_run_elapsed(self):
        dur = timedelta(seconds=round(self._run_elapsed))
        return str(dur)

    def _get_elapsed(self):
        dur = timedelta(seconds=round(self._elapsed))
        return str(dur)

    def _get_total_time(self):
        dur = timedelta(seconds=round(self._total_time))
        return str(dur)

    def _get_remaining(self):
        if not self._total_time:
            dur = NULL_STR
        else:
            dur = timedelta(seconds=round(self._total_time - self._elapsed))
        return str(dur)


# ============= EOF =============================================
