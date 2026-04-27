# ===============================================================================
# Copyright 2013 Jake Ross
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

import time
from datetime import datetime
from threading import Event
from math import isfinite

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import Any, List, CInt, Int, Bool, Enum, Str, Instance, Float

from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.consoleable import Consoleable
from pychron.pychron_constants import AR_AR, SIGNAL, BASELINE, WHIFF, SNIFF, FAILED


class DataCollector(Consoleable):
    """
    Base class for ``Collector`` objects. Provides logic for iterative measurement.
    """

    measurement_script = Any
    automated_run = Instance(
        "pychron.experiment.automated_run.automated_run.AutomatedRun"
    )
    measurement_result = Str

    detectors = List
    check_conditionals = Bool(True)
    ncounts = CInt

    is_baseline = Bool(False)
    for_peak_hop = Bool(False)
    fits = List
    series_idx = Int
    fit_series_idx = Int

    canceled = False
    terminated = False

    _truncate_signal = False
    starttime = None
    starttime_abs = None

    _alive = False
    _evt = None
    _warned_no_fit = None
    _warned_no_det = None

    collection_kind = Enum((SNIFF, WHIFF, BASELINE, SIGNAL))
    refresh_age = False
    _data = None
    _temp_conds = None
    _result = None
    _queue = None
    _plot_data_buffers = None
    _last_plot_panel_update = 0
    _live_plot_limits = None

    err_message = Str
    no_intensity_threshold = 100
    not_intensity_count = 0
    trigger = None
    plot_panel_update_period = Int(1)
    plot_panel_update_min_period = Float(0.25)

    def __init__(self, *args, **kw):
        super(DataCollector, self).__init__(*args, **kw)
        bind_preference(
            self,
            "plot_panel_update_period",
            "pychron.experiment.plot_panel_update_period",
        )

    # def wait(self):
    #     st = time.time()
    #     self.debug('wait started')
    #     while 1:
    #         if self._evt and self._evt.set():
    #             break
    #     self.debug('wait complete {:0.1f}s'.format(time.time() - st))

    def set_truncated(self):
        self._truncate_signal = True

    def stop(self):
        self._alive = False
        if self._evt:
            self._evt.set()

    def set_starttime(self, s):
        self.starttime = s
        if s is not None:
            # convert s (result of time.time()) to a datetime object
            self.starttime_abs = datetime.fromtimestamp(s)

    def measure(self):
        if self.canceled:
            return

        self.measurement_result = ""
        self.terminated = False
        self._truncate_signal = False
        self._warned_no_fit = []
        self._warned_no_det = []
        self._plot_data_buffers = {}
        self._live_plot_limits = {}
        self._last_plot_panel_update = 0

        if self.starttime is None:
            self.starttime = time.time()
            self.starttime_abs = datetime.now()

        et = self.ncounts * self.period_ms * 0.001

        self._alive = True

        self._measure()

        tt = time.time() - self.starttime
        self.debug("estimated time: {:0.3f} actual time: :{:0.3f}".format(et, tt))

    # def plot_data(self, *args, **kw):
    #     from pychron.core.ui.gui import invoke_in_main_thread
    #     invoke_in_main_thread(self._plot_data, *args, **kw)

    def set_temporary_conditionals(self, cd):
        self._temp_conds = cd

    def clear_temporary_conditionals(self):
        self._temp_conds = None

    # private
    def _measure(self):
        self.debug("starting measurement")

        self._evt = evt = Event()

        # self._queue = q = Queue()
        # def writefunc():
        #     writer = self.data_writer
        #     while not q.empty() or not evt.wait(10):
        #         dets = self.detectors
        #         while not q.empty():
        #             x, keys, signals = q.get()
        #             writer(dets, x, keys, signals)
        #
        # # only write to file every 10 seconds and not on main thread
        # t = Thread(target=writefunc)
        # # t.setDaemon(True)
        # t.start()

        self.debug("measurement period (ms) = {}".format(self.period_ms))
        period = self.period_ms * 0.001
        i = 1

        while not evt.is_set():
            result = self._check_iteration(i)
            if not result:
                if not self._pre_trigger_hook():
                    break

                if self.trigger:
                    self.trigger()

                evt.wait(period)
                
                # Defer plot panel count update to main thread to avoid Qt operations on worker thread
                # This prevents spinning wheel freeze from main thread responding to worker thread Qt signals
                invoke_in_main_thread(self._update_plot_panel_counts, i)
                
                inc = self._iter_hook(i)
                if inc is None:
                    break

                self._post_iter_hook(i)
                if inc:
                    i += 1
            else:
                if result == "cancel":
                    self.canceled = True
                elif result == "terminate":
                    self.terminated = True
                break

        evt.set()
        self._flush_plot_buffers(force=True)
        # self.debug('waiting for write to finish')
        # t.join()

        self.debug("measurement finished")

    def _update_plot_panel_counts(self, count):
        """Update plot panel counts on main thread to avoid Qt operations on worker thread."""
        if self.automated_run and self.automated_run.plot_panel:
            self.automated_run.plot_panel.counts = count

    def _update_plot_panel_visual(self):
        """Update plot panel visuals on main thread to avoid Qt operations on worker thread."""
        if self.plot_panel:
            self.plot_panel.update()

    def _adjust_plot_panel_total_counts(self, delta):
        """Adjust plot panel total counts on main thread to avoid Qt operations on worker thread."""
        if self.plot_panel:
            self.plot_panel.total_counts -= delta

    def _post_iter_hook(self, i):
        self._flush_plot_buffers(cnt=i)
        if self.experiment_type == AR_AR and self.refresh_age and not i % 5:
            self.isotope_group.calculate_age(force=True)

    def _pre_trigger_hook(self):
        return True

    def _iter_hook(self, i):
        return self._iteration(i)

    def _iteration(self, i: int, detectors=None):
        try:
            data = self._get_data(detectors)
            if not data:
                return

            k, s, t, inc = data
        except (AttributeError, TypeError, ValueError) as e:
            self._handle_iteration_exception(e)
            return

        if k is not None and s is not None:
            x = self._get_time(t)
            self._save_data(x, k, s)
            self._plot_data(i, x, k, s)

        return inc

    def _handle_iteration_exception(self, exc: Exception) -> None:
        message = "Measurement failed getting data: {}".format(exc)
        self.err_message = message
        self.warning(message)
        self.debug_exception()
        self.canceled = True

        if self.automated_run is not None:
            self.automated_run.cancel_run(
                state=FAILED, do_post_equilibration=False
            )

    def _get_time(self, t):
        if t is None:
            t = time.time()
            r = t - self.starttime
        else:
            # t is provided by the spectrometer. t should be a python datetime object
            # since t is in absolute time use self.starttime_abs
            r = t - self.starttime_abs

            # convert to seconds
            r = r.total_seconds()

        return r

    def _get_data(self, detectors=None):
        try:
            data = next(self.data_generator)
        except StopIteration:
            self.debug("data generator stopped")
            return
        if data:
            keys, signals, ct, inc = data
            if keys is not None and signals is not None:
                if detectors:
                    # data = list(zip(*(d for d in zip(*data) if d[0] in detectors)))
                    nkeys, nsignals = [], []
                    for k, s in zip(keys, signals):
                        if k in detectors:
                            nkeys.append(k)
                            nsignals.append(s)

                    ds = (nkeys, nsignals, ct, inc)

                else:
                    ds = (keys, signals, ct, inc)

                self._data = ds
            return data

    def _save_data(self, x, keys, signals):
        # self._queue.put((x, keys, signals))
        self.data_writer(self.detectors, x, keys, signals)

        # update arar_age
        if self.is_baseline and self.for_peak_hop:
            self._update_baseline_peak_hop(x, keys, signals)
        else:
            self._update_isotopes(x, keys, signals)

    def _update_baseline_peak_hop(self, x, keys, signals):
        ig = self.isotope_group
        for iso in ig.itervalues():
            signal = self._get_signal(keys, signals, iso.detector)
            if signal is not None:
                if not ig.append_data(iso.name, iso.detector, x, signal, "baseline"):
                    self.debug(
                        "baselines - failed appending data for {}. "
                        "not a current isotope {}".format(iso, ig.isotope_keys)
                    )

    def _update_isotopes(self, x, keys, signals):
        a = self.isotope_group
        kind = self.collection_kind

        for dn in keys:
            dn = self._get_detector(dn)
            if dn:
                iso = dn.isotope
                if iso:
                    signal = self._get_signal(keys, signals, dn.name)
                    if signal is not None:
                        if not a.append_data(iso, dn.name, x, signal, kind):
                            self.debug(
                                "{} - failed appending data for {}. not a current isotope {}".format(
                                    kind, iso, a.isotope_keys
                                )
                            )

    def _get_signal(self, keys, signals, det):
        try:
            return signals[keys.index(det)]
        except ValueError:
            if det not in self._warned_no_det:
                self.warning("Detector {} is not available".format(det))
                self._warned_no_det.append(det)
                self.canceled = True
                self.stop()

    def _get_detector(self, d):
        if isinstance(d, str):
            d = next((di for di in self.detectors if di.name == d), None)
        return d

    def _plot_data(self, cnt, x, keys, signals):
        for dn, signal in zip(keys, signals):
            det = self._get_detector(dn)
            if det:
                self._set_plot_data(cnt, det, x, signal)

    def _set_plot_data(self, cnt, det, x, signal):
        iso = det.isotope
        detname = det.name
        ypadding = det.ypadding
        gs = []
        if self.collection_kind == SNIFF:
            if iso:
                gs = [
                    (self.plot_panel.sniff_graph, iso, None, 0, 0),
                    (self.plot_panel.isotope_graph, iso, None, 0, 0),
                ]
        elif self.collection_kind == BASELINE:
            iso = self.isotope_group.get_isotope(detector=detname, kind="baseline")
            if iso is not None:
                fit = iso.get_fit(cnt)
            else:
                fit = "average"
            gs = [(self.plot_panel.baseline_graph, detname, fit, 0, 0)]
        elif iso:
            title = self.isotope_group.get_isotope_title(name=iso, detector=detname)
            iso = self.isotope_group.get_isotope(name=iso, detector=detname)
            fit = iso.get_fit(cnt)
            gs = [
                (
                    self.plot_panel.isotope_graph,
                    title,
                    fit,
                    self.series_idx,
                    self.fit_series_idx,
                )
            ]

        for g, name, fit, series, fit_series in gs:
            pid = g.get_plotid_by_ytitle(name)
            if pid is None:
                # this case arises when doing a sniff and a peakhop.
                # the sniff graph and the signal graph have different plots and its ok not to warn about this
                if not self.collection_kind == SNIFF:
                    self.critical(
                        "failed to locate {}, ytitles={}".format(
                            name, g.get_plot_ytitles()
                        )
                    )
                continue

            self._queue_plot_data(
                g, pid, series, fit_series, fit, x, signal, ypadding
            )

    def _queue_plot_data(
        self, graph, plotid, series, fit_series, fit, x, signal, ypadding
    ):
        key = (id(graph), plotid, series, fit_series)
        buf = self._plot_data_buffers.get(key)
        if buf is None:
            buf = {
                "graph": graph,
                "plotid": plotid,
                "series": series,
                "fit_series": fit_series,
                "fit": fit,
                "ypadding": ypadding,
                "xs": [],
                "ys": [],
            }
            self._plot_data_buffers[key] = buf

        buf["xs"].append(x)
        buf["ys"].append(signal)
        buf["fit"] = fit
        buf["ypadding"] = ypadding

    def _flush_plot_buffers(self, cnt=None, force=False):
        if not self.plot_panel or not self._plot_data_buffers:
            return

        now = time.time()
        if not force and not self._should_refresh_plot_panel(cnt, now):
            return

        # Collect buffer data to pass to main thread
        buffers_to_flush = list(self._plot_data_buffers.values())
        self._plot_data_buffers.clear()
        
        # Defer all graph updates to main thread to avoid Qt operations on worker thread
        invoke_in_main_thread(self._flush_plot_buffers_on_main_thread, buffers_to_flush)
        
        self._last_plot_panel_update = now
    
    def _flush_plot_buffers_on_main_thread(self, buffers):
        """Flush plot buffers on main thread to avoid Qt operations on worker thread."""
        for buf in buffers:
            xs = buf["xs"]
            ys = buf["ys"]
            if not xs:
                continue

            graph = buf["graph"]
            graph.add_bulk_data(
                xs,
                ys,
                plotid=buf["plotid"],
                series=buf["series"],
                ypadding=buf["ypadding"],
                update_y_limits=False,
            )
            self._update_live_plot_limits(
                graph,
                plotid=buf["plotid"],
                series=buf["series"],
                xs=xs,
                ys=ys,
                ypadding=buf["ypadding"],
            )
            fit = buf["fit"]
            if fit:
                graph.set_fit(fit, plotid=buf["plotid"], series=buf["fit_series"])
        
        # Update plot panel visuals
        if self.plot_panel:
            self.plot_panel.update()

    def _should_refresh_plot_panel(self, cnt, now):
        period = max(1, self.plot_panel_update_period)
        period_ready = cnt is not None and not cnt % period
        time_ready = (
            self._last_plot_panel_update == 0
            or now - self._last_plot_panel_update >= self.plot_panel_update_min_period
        )
        return period_ready or time_ready

    def _update_live_plot_limits(self, graph, plotid, series, xs, ys, ypadding):
        key = (id(graph), plotid, series, self.collection_kind)
        state = self._live_plot_limits.get(key)
        if state is None:
            state = {
                "min": None,
                "max": None,
                "recalc_count": 0,
            }
            self._live_plot_limits[key] = state

        batch_min = min(ys)
        batch_max = max(ys)
        state["min"] = batch_min if state["min"] is None else min(state["min"], batch_min)
        state["max"] = batch_max if state["max"] is None else max(state["max"], batch_max)

        all_ys = graph.get_data(plotid=plotid, series=series, axis=1)
        if len(all_ys):
            observed_min = all_ys.min()
            observed_max = all_ys.max()
            state["recalc_count"] += 1

            # Shrink stale limits only occasionally so the live plot stays stable.
            if state["recalc_count"] >= 4:
                state["min"] = observed_min
                state["max"] = observed_max
                state["recalc_count"] = 0

        ymin, ymax = state["min"], state["max"]
        if ymin is None or ymax is None:
            return

        if isinstance(ypadding, str):
            ypad = abs(ymax - ymin) * float(ypadding)
        else:
            ypad = ypadding

        # Only anchor to 0 if ymin is small relative to the data range
        # This prevents forcing data at 400±1 to plot from 0-401+
        data_range = ymax - ymin
        should_anchor_to_zero = (
            self.collection_kind in (SIGNAL, SNIFF)
            and ymin >= 0
            and data_range > 0
            and ymin <= 0.5 * data_range  # Only if ymin is < 50% of range
        )
        
        if should_anchor_to_zero:
            ymin = 0
        else:
            ymin -= ypad
        ymax += ypad

        if isfinite(ymin) and isfinite(ymax):
            graph.set_y_limits(min_=ymin, max_=ymax, plotid=plotid, force=False)

        xmax = max(xs)
        self._update_live_x_limits(graph, plotid, xmax)

    def _update_live_x_limits(self, graph, plotid, xmax):
        expected = None
        if self.plot_panel is not None:
            expected = self.plot_panel._ncounts * self.plot_panel.integration_time

        _, current_max = graph.get_x_limits(plotid)
        candidates = [xmax * 1.05]
        if expected:
            candidates.append(expected)
        if current_max is not None:
            candidates.append(current_max)

        graph.set_x_limits(min_=0, max_=max(candidates), plotid=plotid, force=False)

    # ===============================================================================
    #
    # ===============================================================================

    # ===============================================================================
    # checks
    # ===============================================================================
    # def _check_modification_conditionals(self, cnt):
    #     tripped = self._check_conditionals(self.modification_conditionals, cnt)
    #     if tripped:
    #         queue = self.automated_run.experiment_executor.experiment_queue
    #         tripped.do_modifications(queue, self.automated_run)
    #         if tripped.use_truncation:
    #             return self._set_run_truncated()

    def _check_conditionals(self, conditionals, cnt):
        self.err_message = ""
        for ti in conditionals:
            if ti.check(self.automated_run, self._data, cnt):
                m = "Conditional tripped: {}".format(ti.to_string())
                self.info(m)
                self.err_message = m
                return ti

    def _equilibration_func(self, tr):
        if tr.use_truncation:
            self.measurement_script.abbreviated_count_ratio = tr.abbreviated_count_ratio
            return self._set_truncated()
        elif tr.use_termination:
            return "terminate"

    def _modification_func(self, tr):
        run = self.automated_run
        ex = run.experiment_executor
        queue = ex.experiment_queue
        tr.do_modifications(run, ex, queue)

        if self.measurement_script is not None:
            self.measurement_script.abbreviated_count_ratio = tr.abbreviated_count_ratio
        if tr.use_truncation:
            return self._set_truncated()
        elif tr.use_termination:
            return "terminate"

    def _truncation_func(self, tr):
        if self.measurement_script is not None:
            self.measurement_script.abbreviated_count_ratio = tr.abbreviated_count_ratio
        return self._set_truncated()

    def _action_func(self, tr):
        tr.perform(self.measurement_script)
        if not tr.resume:
            return "break"

    def _set_truncated(self):
        self.state = "truncated"
        self.automated_run.truncated = True
        self.automated_run.spec.transition("truncate", source="data_collector")
        return "break"

    def _check_iteration(self, i):
        if self._temp_conds:
            ti = self._check_conditionals(self._temp_conds, i)
            if ti:
                self.measurement_result = ti.action
                return "break"

        j = i - 1
        user_counts = 0 if self.plot_panel is None else self.plot_panel.ncounts
        script_counts = (
            0 if self.measurement_script is None else self.measurement_script.ncounts
        )
        original_counts = self.ncounts
        count_args = (j, original_counts)

        # self.debug('user_counts={}, script_counts={}, original_counts={}'.format(user_counts,
        #                                                                          script_counts,
        #                                                                          original_counts))

        if not self._alive:
            self.info("measurement iteration executed {}/{} counts".format(*count_args))
            return "cancel"

        if user_counts != original_counts:
            if i > user_counts:
                self.info(
                    "user termination. measurement iteration executed {}/{} counts".format(
                        *count_args
                    )
                )
                invoke_in_main_thread(self._adjust_plot_panel_total_counts, original_counts - i)
                return self._set_truncated()

        elif script_counts != original_counts:
            if i > script_counts:
                self.info(
                    "script termination. measurement iteration executed {}/{} counts".format(
                        *count_args
                    )
                )
                return self._set_truncated()

        elif i > original_counts:
            return "break"

        if self._truncate_signal:
            self.info("measurement iteration executed {}/{} counts".format(*count_args))
            self._truncate_signal = False
            return self._set_truncated()

        if self.check_conditionals:
            result = self._check_run_conditionals(i, j, original_counts)
            if result:
                return result

    def _check_run_conditionals(self, i, executed_counts, original_counts):
        for tag, func, conditionals in self._iter_conditionals():
            tripped = self._check_conditionals(conditionals, i)
            if tripped:
                self.info(
                    "{} conditional {}. measurement iteration executed {}/{} counts".format(
                        tag, tripped.message, executed_counts, original_counts
                    ),
                    color="red",
                )
                self.automated_run.show_conditionals(tripped=tripped)
                return func(tripped)

    def _iter_conditionals(self):
        for tag, func, conditionals in (
            ("modification", self._modification_func, self.modification_conditionals),
            ("truncation", self._truncation_func, self.truncation_conditionals),
            ("action", self._action_func, self.action_conditionals),
            ("termination", lambda x: "terminate", self.termination_conditionals),
            ("cancelation", lambda x: "cancel", self.cancelation_conditionals),
            ("equilibration", self._equilibration_func, self.equilibration_conditionals),
        ):
            if tag == "equilibration" and self.collection_kind != SNIFF:
                continue
            if conditionals:
                yield tag, func, conditionals

    @property
    def isotope_group(self):
        if self.automated_run:
            return self.automated_run.isotope_group

    @property
    def plot_panel(self):
        if self.automated_run:
            return self.automated_run.plot_panel

    @property
    def modification_conditionals(self):
        if self.automated_run:
            return self.automated_run.modification_conditionals

    @property
    def truncation_conditionals(self):
        if self.automated_run:
            return self.automated_run.truncation_conditionals

    @property
    def termination_conditionals(self):
        if self.automated_run:
            return self.automated_run.termination_conditionals

    @property
    def action_conditionals(self):
        if self.automated_run:
            return self.automated_run.action_conditionals

    @property
    def cancelation_conditionals(self):
        if self.automated_run:
            return self.automated_run.cancelation_conditionals

    @property
    def equilibration_conditionals(self):
        if self.automated_run:
            return self.automated_run.equilibration_conditionals


# ============= EOF =============================================
