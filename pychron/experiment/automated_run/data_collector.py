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
from traits.api import Any, List, CInt, Int, Bool, Enum, Str
# from traitsui.api import View, Item
# from pyface.timer.do_later import do_after
# ============= standard library imports ========================
import time
from threading import Event, Timer
# ============= local library imports  ==========================
from pychron.envisage.consoleable import Consoleable
# from pychron.core.ui.gui import invoke_in_main_thread
from pychron.experiment.utilities.conditionals_results import check_conditional_results
from pychron.globals import globalv
from pychron.consumer_mixin import consumable
# from pychron.core.codetools.memory_usage import mem_log


class DataCollector(Consoleable):
    """
    Base class for ``Collector`` objects. Provides logic for iterative measurement.
    """

    measurement_script = Any
    # plot_panel = Any
    # arar_age = Any
    automated_run = Any
    measurement_result = Str

    detectors = List
    check_conditionals = Bool(True)
    # truncation_conditionals = List
    # termination_conditionals = List
    # action_conditionals = List
    ncounts = CInt
    #grpname = Str

    is_baseline = Bool(False)
    for_peak_hop = Bool(False)
    fits = List
    series_idx = Int
    fit_series_idx = Int
    #total_counts = CInt

    canceled = False
    terminated = False

    _truncate_signal = False
    starttime = None
    _alive = False
    _evt = None
    _warned_no_fit = None
    _warned_no_det = None

    collection_kind = Enum(('sniff', 'signal', 'baseline'))
    refresh_age = False
    _data = None
    _temp_conds = None
    _result = None

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

        #wait for graphs to be fully constructed in the MainThread
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

    def _measure(self, evt):
        self.debug('starting measurment')
        with consumable(func=self._iter_step) as con:
            self._iter(con, evt, 1)
            while not evt.is_set():
                time.sleep(0.05)

        self.debug('measurement finished')

    def _iter(self, con, evt, i, prev=0):

        result = self._check_iteration(evt, i)

        if not result:
            try:
                if i <= 1:
                    self.automated_run.plot_panel.counts = 1
                else:
                    self.automated_run.plot_panel.counts += 1
            except AttributeError:
                pass

            if not self._iter_hook(con, i):
                evt.set()
                return

            ot = time.time()
            p = self.period_ms * 0.001
            t = Timer(max(0, p - prev), self._iter, args=(con, evt, i + 1,
                                                          time.time() - ot))

            t.name = 'iter_{}'.format(i + 1)
            t.start()

        else:
            if result == 'cancel':
                self.canceled = True
            elif result == 'terminate':
                self.terminated = True

            #self.debug('no more iter')
            evt.set()

    def _iter_hook(self, con, i):
        return True

    def _iter_step(self, data):
        pass

    def _get_data(self, dets=None):
        data = self.data_generator.next()
        if dets:
            data = zip(*[(k, s) for k, s in zip(*data)
                         if k in dets])
        self._data = data
        return data

    def _save_data(self, x, keys, signals):
        self.data_writer(self.detectors, x, keys, signals)
        #update arar_age
        if self.is_baseline and self.for_peak_hop:
            self._update_baseline_peak_hop(x, keys, signals)
        else:
            self._update_isotopes(x, keys, signals)

        if self.refresh_age:
            self.arar_age.calculate_age(force=True)

    def _update_baseline_peak_hop(self, x, keys, signals):
        a = self.arar_age
        for iso in self.arar_age.isotopes.itervalues():
            signal = self._get_signal(keys, signals, iso.detector)
            if signal is not None:
                if not a.append_data(iso.name, iso.detector, x, signal, 'baseline'):
                    self.debug('baselines - failed appending data for {}. not a current isotope {}'.format(iso,
                                                                                                           a.isotope_keys))

    def _update_isotopes(self, x, keys, signals):
        a = self.arar_age
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
            if not det in self._warned_no_det:
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
        for k, v in self.arar_age.isotopes.iteritems():
            signal = signals[keys.index(v.detector)]
            self._set_plot_data(i, k, v.detector, x, signal)

    def _plot_data_(self, cnt, x, keys, signals):
        for i, dn in enumerate(keys):
            dn = self._get_detector(dn)
            if dn:
                iso = dn.isotope
                signal = signals[keys.index(dn.name)]
                self._set_plot_data(cnt, iso, dn.name, x, signal)

    def _get_fit(self, cnt, det, iso):
        isotopes = self.arar_age.isotopes
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

        #get fit and name
        fit, name = self._get_fit(cnt, det, iso)
        # print fit, name, det, iso
        graph = self.plot_panel.isotope_graph
        pid = graph.get_plotid_by_ytitle(name)
        if pid is not None:
            # print self.series_idx, self.fit_series_idx
            # print graph.plots[pid].plots
            graph.add_datum((x, signal),
                            series=self.series_idx,
                            plotid=pid,
                            update_y_limits=True,
                            ypadding='0.1')

            if fit:
                graph.set_fit(fit, plotid=pid, series=self.fit_series_idx)

    def _plot_data(self, i, x, keys, signals):
        if globalv.experiment_debug:
            x *= (self.period_ms * 0.001) ** -1

        if self.is_baseline and self.for_peak_hop:
            self._plot_baseline_for_peak_hop(i, x, keys, signals)
        else:
            self._plot_data_(i, x, keys, signals)

        graph = self.plot_panel.isotope_graph
        graph.refresh()

    # ===============================================================================
    #
    # ===============================================================================

    # ===============================================================================
    # checks
    # ===============================================================================
    def _check_conditionals(self, conditionals, cnt):
        for ti in conditionals:
            if ti.check(self.automated_run, self._data, cnt):
                return ti

    def _check_iteration(self, evt, i):
        if evt and evt.isSet():
            return True

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
                return 'break'
        elif script_counts != original_counts:
            print script_counts, original_counts, i
            if i > script_counts:
                self.info('script termination. measurement iteration executed {}/{} counts'.format(*count_args))
                return 'break'
        elif i > original_counts:
            return 'break'

        if self._truncate_signal:
            self.info('measurement iteration executed {}/{} counts'.format(*count_args))
            self._truncate_signal = False

            return 'break'

        if self.check_conditionals:
            termination_conditional = self._check_conditionals(self.termination_conditionals, i)
            if termination_conditional:
                self.info('termination conditional {}. measurement iteration executed {}/{} counts'.format(
                    termination_conditional.message, j, original_counts), color='red')

                key = repr(termination_conditional)
                n = termination_conditional.nfails
                if check_conditional_results(key, n):
                    return 'cancel'
                else:
                    return 'terminated'

            cancelation_conditional = self._check_conditionals(self.cancelation_conditionals, i)
            if cancelation_conditional:
                self.info('cancelation conditional {}. measurement iteration executed {}/{} counts'.format(
                    cancelation_conditional.message, j, original_counts), color='red')
                self.automated_run.show_conditionals(tripped=cancelation_conditional)
                return 'cancel'

            truncation_conditional = self._check_conditionals(self.truncation_conditionals, i)
            if truncation_conditional:
                self.info('truncation conditional {}. measurement iteration executed {}/{} counts'.format(
                    truncation_conditional.message, j, original_counts), color='red')
                self.state = 'truncated'
                self.measurement_script.abbreviated_count_ratio = truncation_conditional.abbreviated_count_ratio
                self.automated_run.show_conditionals(tripped=truncation_conditional)
                #                self.condition_truncated = True
                return 'break'

            action_conditional = self._check_conditionals(self.action_conditionals, i)
            if action_conditional:
                self.info(
                    'action conditional {}. measurement iteration executed {}/{} counts'.format(
                        action_conditional.message,
                        j, original_counts), color='red')
                self.automated_run.show_conditionals(tripped=action_conditional)
                action_conditional.perform(self.measurement_script)
                if not action_conditional.resume:
                    return 'break'

    @property
    def arar_age(self):
        return self.automated_run.arar_age

    @property
    def plot_panel(self):
        return self.automated_run.plot_panel

    @property
    def truncation_conditionals(self):
        return self.automated_run.truncation_conditionals

    @property
    def termination_conditionals(self):
        return self.automated_run.termination_conditionals

    @property
    def action_conditionals(self):
        return self.automated_run.action_conditionals

    @property
    def cancelation_conditionals(self):
        return self.automated_run.cancelation_conditionals

# ============= EOF =============================================
