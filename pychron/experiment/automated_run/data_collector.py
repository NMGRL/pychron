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
from queue import Queue
from threading import Event, Thread

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import Any, List, CInt, Int, Bool, Enum, Str, Instance

from pychron.envisage.consoleable import Consoleable
from pychron.pychron_constants import AR_AR, SIGNAL, BASELINE, WHIFF, SNIFF


class DataCollector(Consoleable):
    """
    Base class for ``Collector`` objects. Provides logic for iterative measurement.
    """

    measurement_script = Any
    automated_run = Instance('pychron.experiment.automated_run.automated_run.AutomatedRun')
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

    err_message = Str
    no_intensity_threshold = 100
    not_intensity_count = 0
    trigger = None
    plot_panel_update_period = Int(1)

    def __init__(self, *args, **kw):
        super(DataCollector, self).__init__(*args, **kw)
        bind_preference(self, 'plot_panel_update_period', 'pychron.experiment.plot_panel_update_period')

    def wait(self):
        st = time.time()
        self.debug('wait started')
        while 1:
            if self._evt and self._evt.set():
                break
        self.debug('wait complete {:0.1f}s'.format(time.time() - st))

    def set_truncated(self):
        self._truncate_signal = True

    def stop(self):
        self._alive = False
        if self._evt:
            self._evt.set()

    def measure(self):
        if self.canceled:
            return

        self.measurement_result = ''
        self.terminated = False
        self._truncate_signal = False
        self._warned_no_fit = []
        self._warned_no_det = []

        st = time.time()
        if self.starttime is None:
            self.starttime = st

        et = self.ncounts * self.period_ms * 0.001
        # evt = self._evt
        # if evt:
        #     evt.set()
        # else:
        #     evt = Event()

        # self._evt = evt
        # evt = Event()
        # evt.clear()
        # self._evt = evt

        self._alive = True

        self._measure()

        tt = time.time() - st
        self.debug('estimated time: {:0.3f} actual time: :{:0.3f}'.format(et, tt))

    def plot_data(self, *args, **kw):
        from pychron.core.ui.gui import invoke_in_main_thread
        invoke_in_main_thread(self._plot_data, *args, **kw)

    def set_temporary_conditionals(self, cd):
        self._temp_conds = cd

    def clear_temporary_conditionals(self):
        self._temp_conds = None

    # private
    def _measure(self):
        self.debug('starting measurement')

        self._queue = q = Queue()
        self._evt = Event()
        evt = self._evt

        def writefunc():
            writer = self.data_writer
            while not q.empty() or not evt.wait(10):
                dets = self.detectors
                while not q.empty():
                    x, keys, signals = q.get()
                    writer(dets, x, keys, signals)

        # only write to file every 10 seconds and not on main thread
        t = Thread(target=writefunc)
        # t.setDaemon(True)
        t.start()

        self.debug('measurement period (ms) = {}'.format(self.period_ms))
        period = self.period_ms * 0.001
        i = 1
        # elapsed = 0
        while not evt.is_set():
            result = self._check_iteration(i)
            if not result:
                if not self._pre_trigger_hook():
                    break

                if self.trigger:
                    self.trigger()

                evt.wait(period)
                self.automated_run.plot_panel.counts = i
                if not self._iter_hook(i):
                    break

                self._post_iter_hook(i)
                i += 1
            else:
                if result == 'cancel':
                    self.canceled = True
                elif result == 'terminate':
                    self.terminated = True
                break

        evt.set()
        self.debug('waiting for write to finish')
        t.join()

        self.debug('measurement finished')

    def _pre_trigger_hook(self):
        return True

    # def _iter(self, i):
    #     # st = time.time()
    #     result = self._check_iteration(i)
    #     # self.debug('check iteration duration={}'.format(time.time() - st))
    #
    #     if not result:
    #         try:
    #             if i <= 1:
    #                 self.automated_run.plot_panel.counts = 1
    #             else:
    #                 self.automated_run.plot_panel.counts += 1
    #         except AttributeError:
    #             pass
    #
    #         if not self._iter_hook(i):
    #             # evt.set()
    #             return
    #
    #         self._post_iter_hook(i)
    #         return True
    #     else:
    #         if result == 'cancel':
    #             self.canceled = True
    #         elif result == 'terminate':
    #             self.terminated = True
    #             # evt.set()

    def _post_iter_hook(self, i):
        if self.experiment_type == AR_AR and self.refresh_age and not i % 5:
            self.isotope_group.calculate_age(force=True)
            # t = Timer(0.05, self.isotope_group.calculate_age, kwargs={'force': True})
            # t.start()

    def _pre_trigger_hook(self):
        return True

    def _iter_hook(self, i):
        return self._iteration(i)

    def _iteration(self, i, detectors=None):
        try:
            data = self._get_data(detectors)
        except (AttributeError, TypeError, ValueError) as e:
            self.debug('failed getting data {}'.format(e))
            return

        if not data:
            return

        k, s = data
        if k is not None and s is not None:
            x = self._get_time()
            self._save_data(x, k, s)
            self._plot_data(i, x, k, s)

        return True

    def _get_time(self):
        return time.time() - self.starttime

    def _get_data(self, detectors=None):
        try:
            data = next(self.data_generator)
        except StopIteration:
            self.debug('data generator stopped')
            return

        if data:
            if detectors:
                data = list(zip(*(d for d in zip(*data) if d[0] in detectors)))
            self._data = data
            return data

    def _save_data(self, x, keys, signals):
        self._queue.put((x, keys, signals))

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
                if not ig.append_data(iso.name, iso.detector, x, signal, 'baseline'):
                    self.debug('baselines - failed appending data for {}. '
                               'not a current isotope {}'.format(iso, ig.isotope_keys))

    def _update_isotopes(self, x, keys, signals):
        a = self.isotope_group
        kind = self.collection_kind

        for dn in keys:
            dn = self._get_detector(dn)
            if dn:
                iso = dn.isotope
                signal = self._get_signal(keys, signals, dn.name)
                if signal is not None:
                    if not a.append_data(iso, dn.name, x, signal, kind):
                        self.debug('{} - failed appending data for {}. not a current isotope {}'.format(kind, iso,
                                                                                                        a.isotope_keys))

    def _get_signal(self, keys, signals, det):
        try:
            return signals[keys.index(det)]
        except ValueError:
            if det not in self._warned_no_det:
                self.warning('Detector {} is not available'.format(det))
                self._warned_no_det.append(det)
                self.canceled = True
                self.stop()

    def _get_detector(self, d):
        if isinstance(d, str):
            d = next((di for di in self.detectors
                      if di.name == d), None)
        return d

    def _plot_data(self, cnt, x, keys, signals):
        for dn, signal in zip(keys, signals):
            det = self._get_detector(dn)
            if det:
                self._set_plot_data(cnt, det.isotope, det.name, x, signal)

        if not cnt % self.plot_panel_update_period:
            self.plot_panel.update()

    def _set_plot_data(self, cnt, iso, det, x, signal):

        if self.collection_kind == SNIFF:
            gs = [(self.plot_panel.sniff_graph, iso, None, 0, 0),
                  (self.plot_panel.isotope_graph, iso, None, 0, 0)]

        elif self.collection_kind == BASELINE:
            iso = self.isotope_group.get_isotope(detector=det, kind='baseline')
            if iso is not None:
                fit = iso.get_fit(cnt)
            else:
                fit = 'average'
            gs = [(self.plot_panel.baseline_graph, det, fit, 0, 0)]
        else:
            title = self.isotope_group.get_isotope_title(name=iso, detector=det)
            iso = self.isotope_group.get_isotope(name=iso, detector=det)
            fit = iso.get_fit(cnt)
            gs = [(self.plot_panel.isotope_graph, title, fit, self.series_idx, self.fit_series_idx)]

        dd = self._get_detector(det)
        ypadding = dd.ypadding

        for g, name, fit, series, fit_series in gs:

            pid = g.get_plotid_by_ytitle(name)
            g.add_datum((x, signal),
                        series=series,
                        plotid=pid,
                        update_y_limits=True,
                        ypadding=ypadding)
            if fit:
                g.set_fit(fit, plotid=pid, series=fit_series)

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
        self.err_message = ''
        for ti in conditionals:
            if ti.check(self.automated_run, self._data, cnt):
                m = 'Conditional tripped: {}'.format(ti.to_string())
                self.info(m)
                self.err_message = m
                return ti

    def _modification_func(self, tr):
        queue = self.automated_run.experiment_executor.experiment_queue
        tr.do_modifications(queue, self.automated_run)

        self.measurement_script.abbreviated_count_ratio = tr.abbreviated_count_ratio
        if tr.use_truncation:
            return self._set_truncated()
        elif tr.use_termination:
            return 'terminate'

    def _truncation_func(self, tr):
        self.measurement_script.abbreviated_count_ratio = tr.abbreviated_count_ratio
        return self._set_truncated()

    def _action_func(self, tr):
        tr.perform(self.measurement_script)
        if not tr.resume:
            return 'break'

    def _set_truncated(self):
        self.state = 'truncated'
        self.automated_run.truncated = True
        self.automated_run.spec.state = 'truncated'
        return 'break'

    def _check_iteration(self, i):
        if self._temp_conds:
            ti = self._check_conditionals(self._temp_conds, i)
            if ti:
                self.measurement_result = ti.action
                return 'break'

        j = i - 1
        user_counts = 0 if self.plot_panel is None else self.plot_panel.ncounts
        script_counts = 0 if self.measurement_script is None else self.measurement_script.ncounts
        original_counts = self.ncounts
        count_args = (j, original_counts)

        # self.debug('user_counts={}, script_counts={}, original_counts={}'.format(user_counts,
        #                                                                          script_counts,
        #                                                                          original_counts))

        if not self._alive:
            self.info('measurement iteration executed {}/{} counts'.format(*count_args))
            return 'cancel'

        if user_counts != original_counts:
            if i > user_counts:
                self.info('user termination. measurement iteration executed {}/{} counts'.format(*count_args))
                self.plot_panel.total_counts -= (original_counts - i)
                return self._set_truncated()

        elif script_counts != original_counts:
            if i > script_counts:
                self.info('script termination. measurement iteration executed {}/{} counts'.format(*count_args))
                return self._set_truncated()

        elif i > original_counts:
            return 'break'

        if self._truncate_signal:
            self.info('measurement iteration executed {}/{} counts'.format(*count_args))
            self._truncate_signal = False
            return self._set_truncated()

        if self.check_conditionals:
            for tag, func, conditionals in (('modification', self._modification_func, self.modification_conditionals),
                                            ('truncation', self._truncation_func, self.truncation_conditionals),
                                            ('action', self._action_func, self.action_conditionals),
                                            ('termination', lambda x: 'terminate', self.termination_conditionals),
                                            ('cancelation', lambda x: 'cancel', self.cancelation_conditionals)):

                tripped = self._check_conditionals(conditionals, i)
                if tripped:
                    self.info('{} conditional {}. measurement iteration executed {}/{} counts'.format(tag,
                                                                                                      tripped.message,
                                                                                                      j,
                                                                                                      original_counts),
                              color='red')
                    self.automated_run.show_conditionals(tripped=tripped)
                    return func(tripped)

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

# ============= EOF =============================================
