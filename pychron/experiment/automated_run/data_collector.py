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

# ============= enthought library imports =======================
import time
from Queue import Queue
from threading import Event, Thread, Timer

from traits.api import Any, List, CInt, Int, Bool, Enum, Str

from pychron.envisage.consoleable import Consoleable
from pychron.globals import globalv
from pychron.pychron_constants import AR_AR, SIGNAL, BASELINE, WHIFF, SNIFF
from pychron.spectrometer.thermo.spectrometer.base import NoIntensityChange


class DataCollector(Consoleable):
    """
    Base class for ``Collector`` objects. Provides logic for iterative measurement.
    """

    measurement_script = Any
    automated_run = Any
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
    no_intensity_threshold = 10
    not_intensity_count = 0

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
        evt = self._evt
        if evt:
            evt.set()
            evt.wait(0.05)
        else:
            evt = Event()

        self._evt = evt
        evt.clear()

        # wait for graphs to be fully constructed in the MainThread
        evt.wait(0.05)

        self._alive = True

        self._measure(evt)

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
    def _measure(self, evt):
        self.debug('starting measurement')

        self._queue = q = Queue()

        def writefunc():
            writer = self.data_writer
            while not q.empty() or not evt.wait(1):
                dets = self.detectors
                while not q.empty():
                    x, keys, signals = q.get()
                    writer(dets, x, keys, signals)

        # only write to file every 1 seconds and not on main thread
        t = Thread(target=writefunc)
        # t.setDaemon(True)
        t.start()

        period = self.period_ms * 0.001
        i = 1
        while not evt.is_set():
            st = time.time()
            if not self._iter(i):
                break

            i += 1
            evt.wait(max(0, period - time.time() + st))
            # time.sleep(max(0, period - et))

        evt.set()
        self.debug('waiting for write to finish')
        t.join()

        self.debug('measurement finished')

    def _iter(self, i):
        # st = time.time()
        result = self._check_iteration(i)
        # self.debug('check iteration duration={}'.format(time.time() - st))

        if not result:
            try:
                if i <= 1:
                    self.automated_run.plot_panel.counts = 1
                else:
                    self.automated_run.plot_panel.counts += 1
            except AttributeError:
                pass

            if not self._iter_hook(i):
                # evt.set()
                return

            self._post_iter_hook(i)
            return True
        else:
            if result == 'cancel':
                self.canceled = True
            elif result == 'terminate':
                self.terminated = True
                # evt.set()

    def _post_iter_hook(self, i):
        if self.experiment_type == AR_AR and self.refresh_age and not i % 5:
            t = Timer(0.05, self.isotope_group.calculate_age, kwargs={'force': True})
            t.start()

    def _iter_hook(self, i):
        return True

    def _iteration(self, i, detectors=None):
        try:
            data = self._get_data(detectors)
            self.not_intensity_count = 0
        except (AttributeError, TypeError, ValueError), e:
            self.debug('failed getting data {}'.format(e))
            return
        except NoIntensityChange:
            self.warning('No Intensity change. Something is wrong. ')
            if self.no_intensity_count > self.no_intensity_threshold:
                return

            self.not_intensity_count+=1
            return True

        if not data:
            return

        # data is tuple (keys[], signals[])
        k, s = data
        if k is not None and s is not None:
            x = self._get_time()
            self._save_data(x, k, s)
            self._plot_data(i, x, k, s)
        # if k and s are both None that means failed to get intensity from spectrometer, but n failures is less than
        # `pychron.experiment.failed_intensity_count_threshold`
        # skip this iteration and try again next time

        return True

    def _get_time(self):
        return time.time() - self.starttime

    def _get_data(self, detectors=None):
        data = next(self.data_generator)
        if data:
            if detectors:
                data = zip(*[d for d in zip(*data) if d[0] in detectors])
            self._data = data
            return data

    def _save_data(self, x, keys, signals):
        # self.data_writer(self.detectors, x, keys, signals)

        self._queue.put((x, keys, signals))

        # update arar_age
        if self.is_baseline and self.for_peak_hop:
            self._update_baseline_peak_hop(x, keys, signals)
        else:
            self._update_isotopes(x, keys, signals)

    def _update_baseline_peak_hop(self, x, keys, signals):
        ig = self.isotope_group
        for iso in ig.isotopes.itervalues():
            signal = self._get_signal(keys, signals, iso.detector)
            if signal is not None:
                if not ig.append_data(iso.name, iso.detector, x, signal, 'baseline'):
                    self.debug('baselines - failed appending data for {}. not a current isotope {}'.format(iso,
                                                                                                           ig.isotope_keys))

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

    def _plot_baseline_for_peak_hop(self, i, x, keys, signals):
        for k, v in self.isotope_group.isotopes.iteritems():
            signal = signals[keys.index(v.detector)]
            self._set_plot_data(i, None, v.detector, x, signal)

    def _plot_data_(self, cnt, x, keys, signals):
        # for i, dn in enumerate(keys):
        #     dn = self._get_detector(dn)
        #     if dn:
        #         iso = dn.isotope
        #         signal = signals[keys.index(dn.name)]
        #         self._set_plot_data(cnt, iso, dn.name, x, signal)

        for dn, signal in zip(keys, signals):
            det = self._get_detector(dn)
            if det:
                self._set_plot_data(cnt, det.isotope, det.name, x, signal)

    def _get_fit(self, cnt, det, iso):

        isotopes = self.isotope_group.isotopes
        if self.is_baseline:
            ix = isotopes[iso]
            fit = ix.baseline.get_fit(cnt)
            name = iso
        else:
            try:
                name = iso
                iso = isotopes[iso]
            except KeyError:
                name = '{}{}'.format(iso, det)
                iso = isotopes[name]

            fit = iso.get_fit(cnt)

        return fit, name

    def _set_plot_data(self, cnt, iso, det, x, signal):
        """
            if is_baseline than use detector to get isotope
        """
        graph = self.plot_panel.isotope_graph
        if iso is None:
            pids = []
            for isotope in self.isotope_group.isotopes.itervalues():
                # print '{:<10s}{:<10s}{:<5s}'.format(isotope.name, isotope.detector, det)
                if isotope.detector == det:
                    pid = graph.get_plotid_by_ytitle(isotope.name)
                    if pid is not None:
                        try:
                            fit, name = self._get_fit(cnt, det, isotope.name)
                        except BaseException, e:
                            self.debug('set_plot_data, is_baseline={} det={}, get_fit {}'.format(self.is_baseline,
                                                                                                 det, e))
                            continue
                        pids.append((pid, fit))
        else:
            try:
                # get fit and name
                fit, name = self._get_fit(cnt, det, iso)
            except AttributeError, e:
                self.debug('set_plot_data, get_fit {}'.format(e))

            pids = [(graph.get_plotid_by_ytitle(name), fit)]

        # if self.is_baseline:
        # print '{:<10s}{:<10s}{} series={} fit_series={}'.format(iso, det, pids, self.series_idx, self.fit_series_idx)

        def update_graph(g, p, f, sidx, fidx):
            g.add_datum((x, signal),
                        series=sidx,
                        plotid=p,
                        update_y_limits=True,
                        ypadding='0.1')
            if f:
                g.set_fit(f, plotid=p, series=fidx)

        for pid, fit in pids:
            if self.collection_kind == SNIFF:
                update_graph(graph, pid, fit, self.series_idx, self.fit_series_idx)

                sgraph = self.plot_panel.sniff_graph
                update_graph(sgraph, pid, None, 0, 0)
            elif self.collection_kind == BASELINE:
                bgraph = self.plot_panel.baseline_graph
                update_graph(bgraph, pid, fit, 0, 0)
                update_graph(graph, pid, fit, self.series_idx, self.fit_series_idx)
            else:
                update_graph(graph, pid, fit, self.series_idx, self.fit_series_idx)

    def _plot_data(self, i, x, keys, signals):
        if globalv.experiment_debug:
            x *= (self.period_ms * 0.001) ** -1

        if self.is_baseline and self.for_peak_hop:
            self._plot_baseline_for_peak_hop(i, x, keys, signals)
        else:
            self._plot_data_(i, x, keys, signals)

        self.plot_panel.update()

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

        def set_truncated():
            self.state = 'truncated'
            self.automated_run.truncated = True
            self.automated_run.spec.state = 'truncated'
            return 'break'

        if not self._alive:
            self.info('measurement iteration executed {}/{} counts'.format(*count_args))
            return 'cancel'

        if user_counts != original_counts:
            if i > user_counts:
                self.info('user termination. measurement iteration executed {}/{} counts'.format(*count_args))
                self.plot_panel.total_counts -= (original_counts - i)
                return set_truncated()

        elif script_counts != original_counts:
            if i > script_counts:
                self.info('script termination. measurement iteration executed {}/{} counts'.format(*count_args))
                return set_truncated()

        elif i > original_counts:
            return 'break'

        if self._truncate_signal:
            self.info('measurement iteration executed {}/{} counts'.format(*count_args))
            self._truncate_signal = False
            return set_truncated()

        if self.check_conditionals:
            def modification_func(tr):
                queue = self.automated_run.experiment_executor.experiment_queue
                tr.do_modifications(queue, self.automated_run)

                self.measurement_script.abbreviated_count_ratio = tr.abbreviated_count_ratio
                if tr.use_truncation:
                    return set_truncated()
                elif tr.use_termination:
                    return 'terminate'

            def truncation_func(tr):
                self.measurement_script.abbreviated_count_ratio = tr.abbreviated_count_ratio
                return set_truncated()

            def action_func(tr):
                tr.perform(self.measurement_script)
                if not tr.resume:
                    return 'break'

            for tag, func, conditionals in (('modification', modification_func, self.modification_conditionals),
                                            ('truncation', truncation_func, self.truncation_conditionals),
                                            ('action', action_func, self.action_conditionals),
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
            # def _iter(self, con, evt, i, prev=0):
            #
            #     result = self._check_iteration(evt, i)
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
            #         if not self._iter_hook(con, i):
            #             evt.set()
            #             return
            #
            #         ot = time.time()
            #         p = self.period_ms * 0.001
            #         t = Timer(max(0, p - prev), self._iter, args=(con, evt, i + 1,
            #                                                       time.time() - ot))
            #
            #         t.name = 'iter_{}'.format(i + 1)
            #         t.start()
            #
            #     else:
            #         if result == 'cancel':
            #             self.canceled = True
            #         elif result == 'terminate':
            #             self.terminated = True
            #
            #         # self.debug('no more iter')
            #         evt.set()
