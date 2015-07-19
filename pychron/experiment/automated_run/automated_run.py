# ===============================================================================
# Copyright 2011 Jake Ross
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

# # ============= enthought library imports =======================
from traits.api import Any, Str, List, Property, \
    Event, Instance, Bool, HasTraits, Float, Int, Long
# ============= standard library imports ========================
import os
import re
import time
import ast
import yaml
import weakref
from itertools import groupby
from threading import Thread, Event as TEvent
from uncertainties import ufloat, nominal_value, std_dev
from numpy import Inf
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import get_path
from pychron.core.helpers.filetools import add_extension
# from pychron.core.codetools.memory_usage import mem_log

from pychron.experiment.automated_run.hop_util import parse_hops
from pychron.experiment.conditional.conditional import TruncationConditional, \
    ActionConditional, TerminationConditional, conditional_from_dict, CancelationConditional, conditionals_from_file
from pychron.experiment.utilities.conditionals import test_queue_conditionals_name
from pychron.experiment.utilities.identifier import convert_identifier
from pychron.experiment.utilities.script import assemble_script_blob

from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR, MEASUREMENT_COLOR, \
    EXTRACTION_COLOR, SCRIPT_KEYS


DEBUG = False


class ScriptInfo(HasTraits):
    measurement_script_name = Str
    extraction_script_name = Str
    post_measurement_script_name = Str
    post_equilibration_script_name = Str


SCRIPTS = {}
WARNED_SCRIPTS = []


class AutomatedRun(Loggable):
    """
    The ``AutomatedRun`` object is used to execute automated analyses.

    It mostly delegates responisbility to other objects.
    It provides an interface for ``MeasurementPyscripts``.
    All measurement script commands have a corresponding function defined here.
    A commands corresponding function is defined as py_{function_name}

    for example ``position_magnet`` calls ``AutomatedRun.py_position_magnet``

    data collection is handled by either ``MultiCollector`` or ``PeakHopCollector``

    persistence (saving to file and database) is handled by ``AutomatedRunPersister``

    An automated run is executed in four steps by the ``ExperimentExecutor``.

    #. start
    #. extraction
    #. measurement

       a. equilibration
       b. post_equilibration

    #. post_measurement

    equilibration and post_equilibration are executed concurrently with the measurement script
    this way equilibration gas can be measured.

    four pyscripts (all optional) are used to program analysis execution

    1. extraction
    2. measurement
    3. post_equilibration
    4. post_measurement

    four types of conditionals are available

    1. termination_conditionals
    2. truncation_conditionals
    3. action_conditionals
    4. cancelation_conditionals
    """

    spectrometer_manager = Any
    extraction_line_manager = Any
    experiment_executor = Any
    ion_optics_manager = Any

    multi_collector = Instance('pychron.experiment.automated_run.multi_collector.MultiCollector')
    peak_hop_collector = Instance('pychron.experiment.automated_run.peak_hop_collector.PeakHopCollector')
    persister = Instance('pychron.experiment.automated_run.persistence.AutomatedRunPersister', ())
    # dvc_persister = Instance('pychron.experiment.dvc.Persister', ())

    xls_persister = Instance('pychron.experiment.automated_run.persistence.ExcelPersister')
    system_health = Instance('pychron.experiment.health.series.SystemHealthSeries')

    collector = Property

    script_info = Instance(ScriptInfo, ())

    runner = Any
    monitor = Any
    plot_panel = Any
    arar_age = Instance('pychron.processing.arar_age.ArArAge')

    spec = Any
    runid = Property
    uuid = Str
    analysis_id = Long
    fits = List
    eqtime = Float

    use_syn_extraction = Bool(False)
    is_first = Bool(False)
    is_last = Bool(False)
    is_peak_hop = Bool(False)

    truncated = Bool
    state = Str('not run')
    measuring = Bool(False)
    dirty = Bool(False)
    update = Event
    # use_dvc = Bool(False)

    measurement_script = Instance('pychron.pyscripts.measurement_pyscript.MeasurementPyScript')
    post_measurement_script = Instance('pychron.pyscripts.extraction_line_pyscript.ExtractionPyScript')
    post_equilibration_script = Instance('pychron.pyscripts.extraction_line_pyscript.ExtractionPyScript')
    extraction_script = Instance('pychron.pyscripts.extraction_line_pyscript.ExtractionPyScript')

    termination_conditionals = List
    truncation_conditionals = List
    action_conditionals = List
    cancelation_conditionals = List

    peak_center = None
    coincidence_scan = None
    info_color = None

    _active_detectors = List
    _peak_center_detectors = List
    _loaded = False
    _measured = False
    _alive = Bool(False)
    _truncate_signal = Bool
    _equilibration_done = False
    _integration_seconds = Float(1.0)

    min_ms_pumptime = Int(60)
    overlap_evt = None

    peak_center_threshold1 = Int(10)
    peak_center_threshold2 = Int(1.25)
    peak_center_threshold_window = Int(10)

    # ===============================================================================
    # pyscript interface
    # ===============================================================================
    def py_generate_ic_mftable(self, detectors, refiso):
        return self._generate_ic_mftable(detectors, refiso)

    def py_whiff(self, ncounts, conditionals, starttime, starttime_offset, series=0, fit_series=0):
        return self._whiff(ncounts, conditionals, starttime, starttime_offset, series, fit_series)

    def py_reset_data(self):
        # self.persister.pre_measurement_save()
        self._persister_action('pre_measurement_save')
        
    def _persister_action(self, func, *args, **kw):
        getattr(self.persister, func)(*args, **kw)
        for p in (self.xls_persister,):
            if p is not None:
                try:
                    getattr(p, func)(*args, **kw)
                except BaseException, e:
                    self.warning('excel persister action failed. func={}, excp={}'.format(func, e))
                    import traceback

                    traceback.print_exc()

    def py_set_integration_time(self, v):
        self.set_integration_time(v)

    def py_is_last_run(self):
        return self.is_last

    def py_define_detectors(self, isotope, det):
        self._define_detectors(isotope, det)

    def py_position_magnet(self, pos, detector, dac=False):
        if not self._alive:
            return
        self._set_magnet_position(pos, detector, dac=dac)

    def py_activate_detectors(self, dets, peak_center=False):
        if not self._alive:
            return

        if not self.spectrometer_manager:
            self.warning('no spectrometer manager')
            return

        if peak_center:
            self._peak_center_detectors = self._set_active_detectors(dets)
        else:
            self._activate_detectors(dets)

    def py_set_fits(self, fits):
        isotopes = self.arar_age.isotopes
        if not fits:
            fits = self._get_default_fits()
        elif len(fits) == 1:
            fits = {i: fits for i in isotopes}
        else:
            fits = dict([f.split(':') for f in fits])

        for k, iso in isotopes.iteritems():
            try:
                fi = fits[k]
            except KeyError:
                fi = 'linear'
                self.warning('No fit for "{}". defaulting to {}. '
                             'check the measurement script "{}"'.format(k, fi, self.measurement_script.name))
            iso.set_fit_blocks(fi)
            self.debug('set "{}" to "{}"'.format(k, fi))

    def py_set_baseline_fits(self, fits):
        isotopes = self.arar_age.isotopes

        if not fits:
            fits = self._get_default_fits(is_baseline=True)
        elif len(fits) == 1:
            fits = {i.detector: fits[0] for i in isotopes.itervalues()}
        elif isinstance(fits, str):
            fits = {i.detector: fits for i in isotopes.itervalues()}
        else:
            fits = dict([f.split(':') for f in fits])

        for k, iso in isotopes.iteritems():
            try:
                fi = fits[iso.detector]
            except KeyError:
                fi = ('average', 'SEM')
                self.warning('No fit for "{}". defaulting to {}. '
                             'check the measurement script "{}"'.format(iso.detector, fi, self.measurement_script.name))

            iso.baseline.set_fit_blocks(fi)
            self.debug('set "{}" to "{}"'.format(iso.detector, fi))

    def py_get_spectrometer_parameter(self, name):
        self.info('getting spectrometer parameter {}'.format(name))
        if self.spectrometer_manager:
            return self.spectrometer_manager.spectrometer.get_parameter(name)

    def py_set_spectrometer_parameter(self, name, v):
        self.info('setting spectrometer parameter {} {}'.format(name, v))
        if self.spectrometer_manager:
            self.spectrometer_manager.spectrometer.set_parameter(name, v)

    def py_data_collection(self, obj, ncounts, starttime, starttime_offset, series=0, fit_series=0, group='signal'):
        if not self._alive:
            return

        if self.plot_panel:
            self.plot_panel.is_baseline = False

        self.persister.build_tables(group, self._active_detectors)

        self.multi_collector.is_baseline = False
        self.multi_collector.fit_series_idx = fit_series

        if self.experiment_executor:
            sc = self.experiment_executor.signal_color
        else:
            sc = 'red'

        check_conditionals = obj == self.measurement_script

        result = self._measure(group,
                               self.persister.get_data_writer(group),
                               ncounts, starttime, starttime_offset,
                               series,
                               check_conditionals, sc, obj)
        return result

    def py_post_equilibration(self, **kw):
        self.do_post_equilibration(**kw)

    def py_equilibration(self, eqtime=None, inlet=None, outlet=None,
                         do_post_equilibration=True,
                         close_inlet=True,
                         delay=None):
        evt = TEvent()
        if not self._alive:
            evt.set()
            return evt

        self.heading('Equilibration Started')
        t = Thread(name='equilibration', target=self._equilibrate, args=(evt,),
                   kwargs=dict(eqtime=eqtime,
                               inlet=inlet,
                               outlet=outlet,
                               delay=delay,
                               close_inlet=close_inlet,
                               do_post_equilibration=do_post_equilibration))
        t.start()

        return evt

    def py_sniff(self, ncounts, starttime, starttime_offset, series=0, block=True):
        if block:
            return self._sniff(ncounts, starttime, starttime_offset, series)
        else:
            t = Thread(target=self._sniff, args=(ncounts, starttime, starttime_offset, series))
            t.start()
            return True

    def py_baselines(self, ncounts, starttime, starttime_offset, mass, detector,
                     series=0, fit_series=0, settling_time=4):

        if not self._alive:
            return

        gn = 'baseline'
        self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Baseline')
        self.persister.build_tables(gn, self._active_detectors)

        ion = self.ion_optics_manager

        if mass:
            if ion is not None:
                if detector is None:
                    detector = self._active_detectors[0].name

                ion.position(mass, detector)

                msg = 'Delaying {}s for detectors to settle'.format(settling_time)
                self.info(msg)
                if self.plot_panel:
                    self.plot_panel.total_counts += settling_time

                self.wait(settling_time, msg)

        if self.plot_panel:
            self.plot_panel._ncounts = ncounts
            self.plot_panel.is_baseline = True

        self.multi_collector.is_baseline = True
        self.multi_collector.fit_series_idx = fit_series
        check_conditionals = True

        self.collector.for_peak_hop = self.plot_panel.is_peak_hop
        self.plot_panel.is_peak_hop = False
        if self.experiment_executor:
            sc = self.experiment_executor.baseline_color
        else:
            sc = 'green'
        result = self._measure(gn,
                               self.persister.get_data_writer(gn),
                               ncounts, starttime,
                               starttime_offset,
                               series,
                               check_conditionals, sc)

        if self.plot_panel:
            bs = dict([(iso.name, iso.baseline.uvalue) for iso in
                       self.arar_age.isotopes.values()])
            self.set_previous_baselines(bs)
            self.plot_panel.is_baseline = False

        self.multi_collector.is_baseline = False

        return result

    def py_define_hops(self, hopstr):
        """
            set the detector each isotope
            add additional isotopes and associated plots if necessary
        """
        if self.plot_panel is None:
            self.plot_panel = self._new_plot_panel(self.plot_panel, stack_order='top_to_bottom')
        # self.warning('Need to call "define_hops(...)" after "activate_detectors(...)"')
        # return

        self.plot_panel.is_peak_hop = True

        key = lambda x: x[0]
        hops = parse_hops(hopstr, ret='iso,det,is_baseline')
        hops = sorted(hops, key=key)
        a = self.arar_age
        g = self.plot_panel.isotope_graph

        _, pb = self.get_previous_blanks()
        pbs = self.get_previous_baselines()
        correct_for_blank = (not self.spec.analysis_type.startswith('blank') and
                             not self.spec.analysis_type.startswith('background'))
        for iso, dets in groupby(hops, key=key):
            dets = list(dets)
            # print iso, dets, dets[0][2]
            if dets[0][2]:
                continue

            add_detector = len(dets) > 1

            for _, di, _ in dets:
                self._add_active_detector(di)
                name = iso
                if iso in a.isotopes:
                    ii = a.isotopes[iso]
                    ii.detector = di
                    a.isotopes.pop(iso)
                else:
                    ii = a.isotope_factory(name=iso, detector=di)
                    if correct_for_blank:
                        if iso in pb:
                            b = pb[iso]
                            ii.set_blank(nominal_value(b), std_dev(b))
                    if iso in pbs:
                        b = pbs[iso]
                        ii.set_baseline(nominal_value(b), std_dev(b))

                plot = g.get_plot_by_ytitle(iso) or g.get_plot_by_ytitle('{}{}'.format(iso, di))
                if plot is None:
                    plot = self.plot_panel.new_plot()
                    pid = g.plots.index(plot)
                    # print 'adding', pid
                    g.new_series(type='scatter', fit='linear', plotid=pid)

                if add_detector:
                    name = '{}{}'.format(name, di)

                a.isotopes[name] = ii
                plot.y_axis.title = name

        self.plot_panel.analysis_view.load(self)

    def py_peak_hop(self, cycles, counts, hops, mftable, starttime, starttime_offset,
                    series=0, fit_series=0, group='signal'):

        if not self._alive:
            return

        self.ion_optics_manager.set_mftable(mftable)

        is_baseline = False
        self.peak_hop_collector.is_baseline = is_baseline
        self.peak_hop_collector.fit_series_idx = fit_series

        if self.plot_panel:
            self.plot_panel.trait_set(is_baseline=is_baseline,
                                      _ncycles=cycles,
                                      hops=hops)

        # required for mass spec
        self.persister.save_as_peak_hop = True

        self.is_peak_hop = True

        self.persister.build_peak_hop_tables(group, hops)
        writer = self.persister.get_data_writer(group)

        check_conditionals = True
        self._add_conditionals()

        ret = self._peak_hop(cycles, counts, hops, group, writer,
                             starttime, starttime_offset, series,
                             check_conditionals)

        self.is_peak_hop = False
        self.ion_optics_manager.set_mftable()

        return ret

    def py_peak_center(self, detector=None, save=True, isotope=None, check_intensity=True, **kw):
        if not self._alive:
            return

        ion = self.ion_optics_manager

        if ion is not None:
            if self.arar_age and check_intensity:
                iso = self.arar_age.get_isotope(isotope)
                v = iso.get_intensity()
                if v < self.peak_center_threshold1:
                    self.debug('peak center: {}={}<{}'.format(isotope, v, self.peak_center_threshold1))
                    xs = iso.xs[-self.peak_center_threshold_window:]
                    xm = xs.mean()
                    if xm < self.peak_center_threshold2:
                        self.warning(
                            'Skipping peak center. intensities to small. {}<{}'.format(xm, self.peak_center_threshold2))
                        return

            if not self.plot_panel:
                p = self._new_plot_panel(self.plot_panel, stack_order='top_to_bottom')
                self.plot_panel = p

            self.debug('peak center started')

            ad = [di.name for di in self._peak_center_detectors
                  if di.name != detector]

            pc = ion.setup_peak_center(detector=[detector] + ad,
                                       plot_panel=self.plot_panel,
                                       isotope=isotope,
                                       **kw)
            self.peak_center = pc
            self.debug('do peak center')

            ion.do_peak_center(new_thread=False, save=save, message='automated run peakcenter', timeout=300)

            if pc.result:
                self._persister_action('save_peak_center_to_file', pc)
                # self.persister.save_peak_center_to_file(pc)

    def py_coincidence_scan(self):
        pass
        # sm = self.spectrometer_manager
        # obj, t = sm.do_coincidence_scan()
        # self.coincidence_scan = obj
        # t.join()

    # ===============================================================================
    # conditionals
    # ===============================================================================
    def py_add_cancelation(self, **kw):
        """
        cancel experiment if teststr evaluates to true
        """
        self._conditional_appender('cancelation', kw, CancelationConditional)

    def py_add_action(self, **kw):
        """
        attr must be an attribute of arar_age

        perform a specified action if teststr evaluates to true
        """
        self._conditional_appender('action', kw, ActionConditional)

    def py_add_termination(self, **kw):
        """
        attr must be an attribute of arar_age

        terminate run and continue experiment if teststr evaluates to true
        """
        self._conditional_appender('termination', kw, TerminationConditional)

    def py_add_truncation(self, **kw):
        """
        attr must be an attribute of arar_age

        truncate measurement and continue run if teststr evaluates to true
        default kw:
        attr='', comp='',start_count=50, frequency=5,
        abbreviated_count_ratio=1.0
        """
        self._conditional_appender('truncation', kw, TruncationConditional)

    def py_clear_conditionals(self):
        self.py_clear_terminations()
        self.py_clear_truncations()
        self.py_clear_actions()
        self.py_clear_cancelations()

    def py_clear_cancelations(self):
        self.cancelation_conditionals = []

    def py_clear_terminations(self):
        self.termination_conditionals = []

    def py_clear_truncations(self):
        self.truncation_conditionals = []

    def py_clear_actions(self):
        self.action_conditionals = []

    # ===============================================================================
    # run termination
    # ===============================================================================
    def cancel_run(self, state='canceled', do_post_equilibration=True):
        """
        terminate the measurement script immediately

        do post termination
            post_eq and post_meas
        don't save run

        """
        # self.multi_collector.canceled = True
        self.collector.canceled = True

        # self.aliquot='##'
        self.persister.save_enabled = False
        # if self.use_dvc:
        #     self.dvc_persister.save_enabled = False

        for s in ('extraction', 'measurement'):
            script = getattr(self, '{}_script'.format(s))
            if script is not None:
                script.cancel()

        if self.peak_center:
            self.debug('cancel peak center')
            self.peak_center.cancel()

        self.do_post_termination(do_post_equilibration=do_post_equilibration)

        self.finish()

        if state:
            if self.state != 'not run':
                self.state = state

    def truncate_run(self, style='normal'):
        """
        truncate the measurement script

        style:
            normal- truncate current measure iteration and continue
            quick- truncate current measure iteration use truncated_counts for following
                    measure iterations

        """
        if self.measuring:
            style = style.lower()
            if style == 'normal':
                self.measurement_script.truncate('normal')
            elif style == 'quick':
                self.measurement_script.truncate('quick')

            # self._truncate_signal = True
            # self.multi_collector.set_truncated()
            self.collector.set_truncated()
            self.truncated = True
            self.state = 'truncated'

    # ===============================================================================
    #
    # ===============================================================================
    def show_conditionals(self, tripped=None):
        self.experiment_executor.show_conditionals(tripped=tripped,
                                                   show_measuring=True, kind='live')

    def teardown(self):
        if self.measurement_script:
            self.measurement_script.automated_run = None

        self.py_clear_conditionals()

    def finish(self):

        if self.monitor:
            self.monitor.stop()

        if self.state not in ('not run', 'canceled', 'success', 'truncated'):
            self.state = 'failed'

        self.stop()

    def stop(self):
        self._alive = False
        self.collector.stop()

    def start(self):
        if self.monitor is None:
            return self._start()

        if self.monitor.monitor():
            try:
                return self._start()
            except AttributeError, e:
                self.warning('failed starting run: {}'.format(e))
        else:
            self.warning('failed to start monitor')

    def is_alive(self):
        return self._alive

    def heading(self, msg, color=None, *args, **kw):
        super(AutomatedRun, self).info(msg, *args, **kw)
        if self.experiment_executor:
            if color is None:
                color = self.info_color

            if color is None:
                color = 'light green'

            self.experiment_executor.heading(msg, color=color, log=False)

    def info(self, msg, color=None, *args, **kw):
        super(AutomatedRun, self).info(msg, *args, **kw)
        if self.experiment_executor:
            if color is None:
                color = self.info_color

            if color is None:
                color = 'light green'

            self.experiment_executor.info(msg, color=color, log=False)

    def get_interpolation_value(self, value):
        """
        value is a string in the format of $VALUE. Search for VALUE first in the options file
        then in the extraction scripts metadata

        :param value:
        :return:
        """
        v = None
        if self.extraction_script:
            for vv in (value, value.upper(), value.lower()):
                try:
                    v = getattr(self.extraction_script, vv)
                except AttributeError:
                    v = self._get_extraction_parameter(vv, None)
                    if v is None:
                        continue
                break

        if v is None:
            self.warning('Could not interpolate {}. Make sure value is defined in either the options file'
                         'or embedded in the extraction scripts metadata. Defaulting to 0'.format(value))
            v = 0

        return v

    def get_device_value(self, dev_name):
        return self.extraction_line_manager.get_device_value(dev_name)

    def get_pressure(self, attr):
        controller, name = attr.split('.')
        return self.extraction_line_manager.get_pressure(controller, name)

    def get_deflection(self, det, current=False):
        return self.spectrometer_manager.spectrometer.get_deflection(det, current)

    def get_detector(self, det):
        return self.spectrometer_manager.spectrometer.get_detector(det)

    def set_integration_time(self, v):
        spectrometer = self.spectrometer_manager.spectrometer
        nv = spectrometer.set_integration_time(v, force=True)
        self._integration_seconds = nv

    def set_magnet_position(self, *args, **kw):
        return self._set_magnet_position(*args, **kw)

    def set_deflection(self, det, defl):
        self.py_set_spectrometer_parameter('SetDeflection', '{},{}'.format(det, defl))

    def protect_detector(self, det, protect):
        protect = 'On' if protect else 'Off'
        self.py_set_spectrometer_parameter('ProtectDetector', '{},{}'.format(det, protect))

    def wait(self, t, msg=''):
        if self.experiment_executor:
            self.experiment_executor.wait(t, msg)
        else:
            time.sleep(t / 10.)

    def wait_for_overlap(self):
        """
            by default overlap_evt is set
            after equilibration finished
        """
        self.info('waiting for overlap signal')
        self._alive = True
        self.overlap_evt = evt = TEvent()
        evt.clear()
        i = 1
        st = time.time()
        while self._alive and not evt.is_set():
            time.sleep(1)
            if i % 5 == 0:
                et = time.time() - st
                self.debug('waiting for overlap signal. elapsed time={:0.2f}'.format(et))
                i = 0
            i += 1

        if not self._alive:
            return

        self.info('overlap signal set')

        overlap, mp = self.spec.overlap

        self.info('starting overlap delay {}'.format(overlap))
        starttime = time.time()
        i = 1
        while self._alive:
            et = time.time() - starttime
            if et > overlap:
                break
            time.sleep(1.0)
            if i % 50 == 0:
                self.debug('waiting overlap delay {}. elapsed time={:0.2f}'.format(overlap, et))
                i = 0
            i += 1

    def post_measurement_save(self):
        if self._measured:
            if self.spectrometer_manager:
                # get current spectrometer values
                # maybe this should be done during pre_measurement_save
                # self.persister.trait_set(spec_dict=self.spectrometer_manager.make_parameters_dict(),
                # defl_dict=self.spectrometer_manager.make_deflections_dict(),
                # gains=self.spectrometer_manager.make_gains_list(),
                # active_detectors=self._active_detectors)
                self._persister_action('trait_set', spec_dict=self.spectrometer_manager.make_parameters_dict(),
                                       defl_dict=self.spectrometer_manager.make_deflections_dict(),
                                       gains=self.spectrometer_manager.make_gains_list(),
                                       active_detectors=self._active_detectors)

            # save to database
            self._persister_action('post_measurement_save')
            # self.persister.post_measurement_save()

            # save analysis. don't cancel immediately
            ret = None
            if self.system_health:
                ret = self.system_health.add_analysis(self)

            executor = self.experiment_executor
            # cancel the experiment if failed to save to the secondary database
            # cancel/terminate if system health returns a value
            if self.persister.secondary_database_fail:
                if executor:
                    executor.cancel(cancel_run=True,
                                    msg=self.persister.secondary_database_fail)
            elif ret == 'cancel':
                if executor:
                    executor.cancel(cancel_run=True,
                                    msg=self.system_health.error_msg)
            elif ret == 'terminate':
                if executor:
                    executor.cancel('run',
                                    cancel_run=True,
                                    msg=self.system_health.error_msg)
            else:
                return True

    def get_previous_blanks(self):
        blanks = None
        pid = 0
        if self.experiment_executor:
            pid, blanks, runid = self.experiment_executor.get_prev_blanks()

        if not blanks:
            blanks = dict(Ar40=ufloat(0, 0),
                          Ar39=ufloat(0, 0),
                          Ar38=ufloat(0, 0),
                          Ar37=ufloat(0, 0),
                          Ar36=ufloat(0, 0))

        return pid, blanks

    def set_previous_blanks(self, pb):
        if self.experiment_executor:
            self.experiment_executor._prev_blanks = pb

    def get_previous_baselines(self):
        baselines = None
        if self.experiment_executor:
            baselines = self.experiment_executor.get_prev_baselines()

        if not baselines:
            baselines = dict(Ar40=ufloat(0, 0),
                             Ar39=ufloat(0, 0),
                             Ar38=ufloat(0, 0),
                             Ar37=ufloat(0, 0),
                             Ar36=ufloat(0, 0))

        return baselines

    def set_previous_baselines(self, pb):
        if self.experiment_executor:
            self.experiment_executor._prev_baselines = pb

    # ===============================================================================
    # setup
    # ===============================================================================
    def setup_persister(self):
        sens = self._get_extraction_parameter('sensitivity_multiplier', default=1)

        # setup persister. mirror a few of AutomatedRunsAttributes
        script_name, script_blob = self._assemble_script_blob()
        eqn, eqb = '', ''
        pb = {}
        auto_save_detector_ic = False

        executor = self.experiment_executor
        if executor:
            queue = executor.experiment_queue

            eqn = queue.name
            eqb = executor.experiment_blob()
            pb = executor.get_prev_blanks()
            auto_save_detector_ic = queue.auto_save_detector_ic
            self.debug('$$$$$$$$$$$$$$$ auto_save_detector_ic={}'.format(auto_save_detector_ic))

        ext_name, ext_blob, ext_path = '', '', ''
        if self.extraction_script:
            ext_name = self.extraction_script.name
            ext_blob = self._assemble_extraction_blob()
            # ext_path = self.extraction_script.script_path()

        ms_name, ms_blob, ms_path, sfods, bsfods = '', '', '', {}, {}
        if self.measurement_script:
            ms_name = self.measurement_script.name
            ms_blob = self.measurement_script.toblob()
            # ms_path = self.measurement_script.script_path()
            sfods, bsfods = self._get_default_fods()

        ext_pos = []
        if self.extraction_script:
            ext_pos = self.extraction_script.get_extraction_positions()

        self._persister_action('trait_set', save_as_peak_hop=False,
                               uuid=self.uuid,
                               run_spec=self.spec,
                               arar_age=self.arar_age,
                               positions=self.spec.get_position_list(),
                               auto_save_detector_ic=auto_save_detector_ic,
                               extraction_positions=ext_pos,
                               sensitivity_multiplier=sens,
                               experiment_queue_name=eqn,
                               experiment_queue_blob=eqb,
                               extraction_name=ext_name,
                               extraction_blob=ext_blob,
                               measurement_name=ms_name,
                               measurement_blob=ms_blob,
                               previous_blank_id=pb[0],
                               previous_blanks=pb[1],
                               runscript_name=script_name,
                               runscript_blob=script_blob,
                               signal_fods=sfods,
                               baseline_fods=bsfods)

    # ===============================================================================
    # doers
    # ===============================================================================
    def start_extraction(self):
        return self._start_script('extraction')

    def start_measurement(self):
        return self._start_script('measurement')

    def do_extraction(self):
        self.debug('do extraction')

        self._persister_action('pre_extraction_save')
        # self.persister.pre_extraction_save()

        self.info_color = EXTRACTION_COLOR
        msg = 'Extraction Started {}'.format(self.extraction_script.name)
        self.heading('{}'.format(msg))
        self.state = 'extraction'

        self.debug('DO EXTRACTION {}'.format(self.runner))
        self.extraction_script.runner = self.runner
        self.extraction_script.manager = self.experiment_executor
        self.extraction_script.set_run_identifier(self.runid)

        syn_extractor = None
        if self.extraction_script.syntax_ok(warn=False):
            if self.use_syn_extraction and self.spec.syn_extraction:
                p = os.path.join(paths.scripts_dir, 'syn_extraction', self.spec.syn_extraction)
                p = add_extension(p, '.yaml')

                if os.path.isfile(p):
                    from pychron.experiment.automated_run.syn_extraction import SynExtractionCollector

                    dur = self.extraction_script.calculate_estimated_duration(force=True)
                    syn_extractor = SynExtractionCollector(arun=weakref.ref(self)(),
                                                           path=p,
                                                           extraction_duration=dur)
                    syn_extractor.start()
                else:
                    self.warning(
                        'Cannot start syn extraction collection. Configuration file does not exist. {}'.format(p))
        else:
            self.warning('Invalid script syntax for "{}"'.format(self.extraction_script.name))
            return
        if self.extraction_script.execute():
            if syn_extractor:
                syn_extractor.stop()

            # report the extraction results
            r = self.extraction_script.output_achieved()
            for ri in r:
                self.info(ri)

            rblob = self.extraction_script.get_response_blob()
            oblob = self.extraction_script.get_output_blob()
            snapshots = self.extraction_script.snapshots

            self._persister_action('post_extraction_save', rblob, oblob, snapshots)
            # self.persister.post_extraction_save(rblob, oblob, snapshots)
            self.heading('Extraction Finished')
            self.info_color = None

            # if overlapping need to wait for previous runs min mass spec pump time
            self._wait_for_min_ms_pumptime()

            return True
        else:
            if syn_extractor:
                syn_extractor.stop()

            self.do_post_equilibration()
            self.do_post_measurement()
            self.finish()

            self.heading('Extraction Finished unsuccessfully', color='red')
            self.info_color = None
            return False

    def do_measurement(self, script=None, use_post_on_fail=True):
        self.debug('do measurement')
        self.debug('L#={} analysis type={}'.format(self.spec.labnumber,
                                                   self.spec.analysis_type))
        if not self._alive:
            self.warning('run is not alive')
            return

        if script is None:
            script = self.measurement_script

        if script is None:
            self.warning('no measurement script')
            return

        script.trait_set(runner=self.runner,
                         manager=self.experiment_executor)

        # use a measurement_script to explicitly define
        # measurement sequence
        self.info_color = MEASUREMENT_COLOR
        msg = 'Measurement Started {}'.format(script.name)
        self.heading('{}'.format(msg))
        self.state = 'measurement'

        self._persister_action('pre_measurement_save')
        # self.persister.pre_measurement_save()

        self.measuring = True
        self._persister_action('trait_set', save_enabled=True)
        # self.persister.save_enabled = True

        if script.execute():
            # mem_log('post measurement execute')
            self.heading('Measurement Finished')
            self.measuring = False
            self.info_color = None

            self._measured = True
            return self.post_measurement_save()

        else:
            if use_post_on_fail:
                self.do_post_equilibration()
                self.do_post_measurement()
            self.finish()

            self.heading('Measurement Finished unsuccessfully', color='red')
            self.measuring = False
            self.info_color = None
            return False

    def do_post_measurement(self, script=None):
        if script is None:
            script = self.post_measurement_script

        if not script:
            return True

        if not self._alive:
            return

        msg = 'Post Measurement Started {}'.format(script.name)
        self.heading('{}'.format(msg))
        # self.state = 'extraction'
        script.runner = self.runner
        script.manager = self.experiment_executor

        if script.execute():
            self.debug('setting _ms_pumptime')
            self.experiment_executor.ms_pumptime_start = time.time()

            self.heading('Post Measurement Finished')
            return True
        else:
            self.heading('Post Measurement Finished unsuccessfully')
            return False

    def do_post_equilibration(self, block=False):
        if block:
            self._post_equilibration()
        else:
            t = Thread(target=self._post_equilibration)
            t.start()

    def _post_equilibration(self):
        if self._equilibration_done:
            return

        self._equilibration_done = True

        if not self._alive:
            return

        if self.post_equilibration_script is None:
            return
        msg = 'Post Equilibration Started {}'.format(self.post_equilibration_script.name)
        self.heading('{}'.format(msg))
        self.post_equilibration_script.runner = self.runner
        self.post_equilibration_script.manager = self.experiment_executor

        if self.post_equilibration_script.execute():
            self.heading('Post Equilibration Finished')
        else:
            self.heading('Post Equilibration Finished unsuccessfully')

    def do_post_termination(self, do_post_equilibration=True):
        oex = self.experiment_executor.executable
        self.experiment_executor.executable = False
        self.heading('Post Termination Started')
        if do_post_equilibration:
            self.do_post_equilibration()

        self.do_post_measurement()

        self.stop()

        self.heading('Post Termination Finished')
        self.experiment_executor.executable = oex

    # ===============================================================================
    # utilities
    # ===============================================================================
    def assemble_report(self):
        signal_string = ''
        signals = self.get_baseline_corrected_signals()
        if signals:
            signal_string = '\n'.join(['{} {} {}'.format(ai.name, ai.isotope,
                                                         signals[ai.isotope])
                                       for ai in self._active_detectors])

        age = ''
        if self.arar_age:
            age = self.arar_age.age
        age_string = 'age={}'.format(age)

        return '''runid={} timestamp={} {}
anaylsis_type={}
# ===============================================================================
# signals
# ===============================================================================
{}
{}
'''.format(self.runid, self.persister.rundate, self.persister.runtime,
           self.spec.analysis_type,
           signal_string, age_string)

    def get_baseline_corrected_signals(self):
        d = dict()
        for k, iso in self.arar_age.isotopes.iteritems():
            d[k] = iso.get_baseline_corrected_value()
        return d

    def setup_context(self, *args, **kw):
        self._setup_context(*args, **kw)

    # ===============================================================================
    # private
    # ===============================================================================
    def _start(self):
        if self._use_arar_age():
            if self.arar_age is None:
                # load arar_age object for age calculation
                from pychron.processing.arar_age import ArArAge

                self.arar_age = ArArAge()

            es = self.extraction_script
            if es is not None:
                # get senstivity multiplier from extraction script
                v = self._get_yaml_parameter(es, 'sensitivity_multiplier', default=1)
                self.arar_age.sensitivity_multiplier = v

            ln = self.spec.labnumber
            ln = convert_identifier(ln)
            if not self.experiment_executor.datahub.load_analysis_backend(ln, self.arar_age):
                self.debug('failed load analysis backend')
                return

        self.py_clear_conditionals()
        # setup default/queue conditionals
        # clear the conditionals for good measure.
        # conditionals should be cleared during teardown.

        try:
            self._add_conditionals()
        except BaseException, e:
            self.warning('Failed adding conditionals {}'.format(e))
            return

        # add queue conditionals
        self._add_queue_conditionals()

        # add default conditionals
        self._add_default_conditionals()

        self.info('Start automated run {}'.format(self.runid))
        self.measuring = False
        self.truncated = False

        self._alive = True

        if self.plot_panel:
            self.plot_panel.total_counts = 0
            self.plot_panel.is_peak_hop = False
            self.plot_panel.is_baseline = False

        self.multi_collector.canceled = False
        self.multi_collector.is_baseline = False
        self.multi_collector.for_peak_hop = False

        self._equilibration_done = False
        self._refresh_scripts()

        # setup the scripts
        ip = self.spec.script_options
        if ip:
            ip = os.path.join(paths.scripts_dir, 'options', add_extension(ip, '.yaml'))

        if self.measurement_script:
            self.measurement_script.reset(weakref.ref(self)())
            # set the interpolation path
            self.measurement_script.interpolation_path = ip

        for si in ('extraction', 'post_measurement', 'post_equilibration'):
            script = getattr(self, '{}_script'.format(si))
            if script:
                self._setup_context(script)
                script.interpolation_path = ip

        # load extraction metadata
        self.eqtime = self._get_extraction_parameter('eqtime', 15)
        self.time_zero_offset = self.spec.collection_time_zero_offset

        # setup persister. mirror a few of AutomatedRunsAttributes
        self.setup_persister()

        return True

    def _generate_ic_mftable(self, detectors, refiso):
        ret = True
        from pychron.experiment.ic_mftable_generator import ICMFTableGenerator

        e = ICMFTableGenerator()
        if not e.make_mftable(self, detectors, refiso):
            ret = False
        return ret

    def _add_default_conditionals(self):
        self.debug('add default conditionals')
        p = get_path(paths.spectrometer_dir, '.*conditionals', ('.yaml', '.yml'))
        if p is not None:
            self.info('adding default conditionals from {}'.format(p))
            self._add_conditionals_from_file(p)
        else:
            self.warning('no Default Conditionals file. {}'.format(p))

    def _add_queue_conditionals(self):
        """
            load queue global conditionals (truncations, actions, terminations)
        """
        self.debug('Add queue conditionals')
        name = self.spec.queue_conditionals_name
        if test_queue_conditionals_name(name):
            p = get_path(paths.queue_conditionals_dir, name, ('.yaml', '.yml'))
            if p is not None:
                self.info('adding queue conditionals from {}'.format(p))
                self._add_conditionals_from_file(p)

            else:
                self.warning('Invalid Conditionals file. {}'.format(p))

    def _add_conditionals_from_file(self, p):
        d = conditionals_from_file(p)
        for k, v in d.items():
            if k in ('actions', 'truncations', 'terminations', 'cancelations'):
                var = getattr(self, '{}_conditionals'.format(k[:-1]))
                var.extend(v)

                # with open(p, 'r') as rfile:
                # yd = yaml.load(rfile)
                # cs = (('TruncationConditional', 'truncation', 'truncations'),
                # ('ActionConditional', 'action', 'actions'),
                # ('TerminationConditional', 'termination', 'terminations'),
                # ('CancelationConditional', 'cancelation', 'cancelations'))
                #     for klass, var, tag in cs:
                #         yl = yd.get(tag)
                #         if not yl:
                #             continue
                #
                #         var = getattr(self, '{}_conditionals'.format(var))
                #         conds = [conditional_from_dict(ti, klass) for ti in yl]
                #         conds = [c for c in conds if c is not None]
                #         if conds:
                #             var.extend(conds)
                #             # for ti in yl:
                #             # cx =
                #             # var.append(cx)

    def _conditional_appender(self, name, cd, klass):
        if not self.arar_age:
            self.warning('No ArArAge to use for conditional testing')
            return

        attr = cd.get('attr')
        if not attr:
            self.debug('no attr for this {} cd={}'.format(name, cd))
            return

        # for 2.0.4 backwards compatiblity
        # comp = dictgetter(cd, ('teststr','check','comp'))
        # if not comp:
        # self.debug('not teststr for this conditional "{}" cd={}'.format(name, cd))
        # return
        #
        # #for 2.0.4 backwards compatiblity
        # start_count = dictgetter(cd, ('start','start_count'))
        # if start_count is None:
        # start_count = 50
        # self.debug('defaulting to start_count={}'.format(start_count))
        #
        # self.info('adding {} {} {} {}'.format(name, attr, comp, start_count))

        if attr == 'age' and self.spec.analysis_type not in ('unknown', 'cocktail'):
            self.debug('not adding because analysis_type not unknown or cocktail')

        if not self.arar_age.has_attr(attr):
            self.warning('invalid {} attribute "{}"'.format(name, attr))
        else:
            obj = getattr(self, '{}_conditionals'.format(name))
            con = conditional_from_dict(cd, klass)
            if con:
                self.info(
                    'adding {} attr="{}" test="{}" start="{}"'.format(name, con.attr, con.teststr, con.start_count))
                obj.append(con)
            else:
                self.warning('Failed adding {}, {}'.format(name, cd))

    def _refresh_scripts(self):
        for name in SCRIPT_KEYS:
            setattr(self, '{}_script'.format(name), self._load_script(name))

    def _get_default_fits_file(self):
        p = self._get_measurement_parameter('default_fits')
        if p:
            dfp = os.path.join(paths.fits_dir, add_extension(p, '.yaml'))
            if os.path.isfile(dfp):
                return dfp
            else:
                self.warning_dialog('Cannot open default fits file: {}'.format(dfp))

    def _get_default_fits(self, is_baseline=False):
        """
            get name of default fits file from measurement docstr
            return dict of iso:fit pairs
        """
        dfp = self._get_default_fits_file()
        if dfp:
            self.debug('using default fits file={}'.format(dfp))
            with open(dfp, 'r') as rfile:
                yd = yaml.load(rfile)
                key = 'baseline' if is_baseline else 'signal'
                fd = {yi['name']: (yi['fit'], yi['error_type']) for yi in yd[key]}
        else:
            self.debug('no default fits file')
            fd = {}

        return fd

    def _get_default_fods(self):
        def extract_fit_dict(fods, yd):
            for yi in yd:
                fod = {'filter_outliers': yi['filter_outliers'],
                       'iterations': yi['filter_iterations'],
                       'std_devs': yi['filter_std_devs']}
                fods[yi['name']] = fod

        sfods, bsfods = {}, {}
        dfp = self._get_default_fits_file()
        if dfp:
            with open(dfp, 'r') as rfile:
                ys = yaml.load(rfile)
                extract_fit_dict(sfods, ys['signal'])
                extract_fit_dict(bsfods, ys['baseline'])

        return sfods, bsfods

    def _start_script(self, name):
        script = getattr(self, '{}_script'.format(name))
        self.debug('start {}'.format(name))
        if not self._alive:
            self.warning('run is not alive')
            return

        if not script:
            self.warning('no {} script'.format(name))
            return

        return True

    def _add_active_detector(self, di):
        spec = self.spectrometer_manager.spectrometer
        det = spec.get_detector(di)
        if not det in self._active_detectors:
            self._active_detectors.append(det)

    def _set_active_detectors(self, dets):
        spec = self.spectrometer_manager.spectrometer
        return [spec.get_detector(n) for n in dets]

    def _define_detectors(self, isotope, det):
        spec = self.spectrometer_manager.spectrometer
        spec.update_isotopes(isotope, det)

    def _activate_detectors(self, dets):
        """
            !!! this is a potential problem !!!
            need more sophisticated way to set up plot panel
            e.g PP has detectors H1, AX but AX, CDD are active.

            need to remove H1 and add CDD.

            or

            if memory leak not a problem simply always "create" new plots
            instead of only clearing data.

            or use both techniques

            if plot panel detectors != active detectors  "create"

        """

        if self.plot_panel is None:
            create = True
        else:
            cd = set([d.name for d in self.plot_panel.detectors])
            ad = set(dets)
            create = cd - ad or ad - cd

        p = self._new_plot_panel(self.plot_panel, stack_order='top_to_bottom')
        self.plot_panel = p

        self._active_detectors = self._set_active_detectors(dets)

        if create:
            p.create(self._active_detectors)
        else:
            # p.clear_displays()
            p.isotope_graph.clear_plots()

        p.show_isotope_graph()

        # for iso in self.arar_age.isotopes:
        self.arar_age.clear_isotopes()
        self.arar_age.clear_error_components()
        self.arar_age.clear_blanks()

        cb = False
        if (not self.spec.analysis_type.startswith('blank')
            and not self.spec.analysis_type.startswith('background')):

            cb = True
            pid, blanks = self.get_previous_blanks()

            for iso, v in blanks.iteritems():
                self.arar_age.set_blank(iso, v)

        for d in self._active_detectors:
            self.arar_age.set_isotope(d.isotope, (0, 0),
                                      detector=d.name,
                                      correct_for_blank=cb)

        self.arar_age.clear_baselines()

        baselines = self.get_previous_baselines()
        for iso, v in baselines.iteritems():
            self.arar_age.set_baseline(iso, v)

        p.analysis_view.load(self)

    def _add_conditionals(self):
        klass_dict = {'actions': ActionConditional, 'truncations': TruncationConditional,
                      'terminations': TerminationConditional, 'cancelations': CancelationConditional}

        t = self.spec.conditionals
        self.debug('adding conditionals {}'.format(t))
        if t:
            p = os.path.join(paths.conditionals_dir, add_extension(t, '.yaml'))
            if os.path.isfile(p):
                self.debug('extract conditionals from file. {}'.format(p))
                with open(p, 'r') as rfile:
                    yd = yaml.load(rfile)
                    for kind, items in yd.iteritems():
                        try:
                            klass = klass_dict[kind]
                            for i in items:
                                try:
                                    # trim off s
                                    if kind.endswith('s'):
                                        kind = kind[:-1]

                                    self._conditional_appender(kind, i, klass)
                                except BaseException, e:
                                    self.debug('Failed adding {}. excp="{}", cd={}'.format(kind, e, i))

                        except KeyError:
                            self.debug('Invalid conditional kind="{}"'.format(kind))
                            #
                            # for c in doc:
                            # try:
                            # attr = c['attr']
                            # comp = c['check']
                            # start = c['start']
                            # freq = c.get('frequency', 1)
                            # acr = c.get('abbreviated_count_ratio', 1)
                            #             self.py_add_truncation(attr, comp, int(start), freq, acr)
                            #         except BaseException:
                            #             self.warning('Failed adding truncation. {}'.format(c))

            else:
                try:
                    c, start = t.split(',')
                    pat = '<=|>=|[<>=]'
                    attr = re.split(pat, c)[0]

                    freq = 1
                    acr = 0.5
                except Exception, e:
                    self.debug('conditionals parse failed {} {}'.format(e, t))
                    return

                self.py_add_truncation(attr=attr, teststr=c,
                                       start_count=int(start),
                                       frequency=freq,
                                       abbreviated_count_ratio=acr)

    def _get_measurement_parameter(self, key, default=None):
        return self._get_yaml_parameter(self.measurement_script, key, default)

    def _get_extraction_parameter(self, key, default=None):
        return self._get_yaml_parameter(self.extraction_script, key, default)

    def _use_arar_age(self):
        ln = self.spec.labnumber
        return ln not in ('dg', 'pa')

    def _new_plot_panel(self, plot_panel, stack_order='bottom_to_top'):
        from pychron.processing.analyses.view.automated_run_view import AutomatedRunAnalysisView

        title = self.runid
        sample, irradiation = self.spec.sample, self.spec.irradiation
        if sample:
            title = '{}   {}'.format(title, sample)
        if irradiation:
            title = '{}   {}'.format(title, irradiation)

        if plot_panel is None:
            from pychron.experiment.plot_panel import PlotPanel

            plot_panel = PlotPanel(
                stack_order=stack_order,
                info_func=self.info,
                arar_age=self.arar_age)

        an = AutomatedRunAnalysisView(analysis_type=self.spec.analysis_type,
                                      analysis_id=self.runid)
        an.load(self)

        plot_panel.trait_set(
            plot_title=title,
            analysis_view=an)

        return plot_panel

    def _convert_valve(self, valve):
        if valve and not isinstance(valve, (tuple, list)):
            if ',' in valve:
                valve = map(str.strip, valve.split(','))
            else:
                valve = (valve, )
        return valve

    def _equilibrate(self, evt, eqtime=15, inlet=None, outlet=None,
                     delay=3,
                     do_post_equilibration=True, close_inlet=True):

        inlet = self._convert_valve(inlet)
        outlet = self._convert_valve(outlet)

        elm = self.extraction_line_manager
        if elm:
            if outlet:
                # close mass spec ion pump
                for o in outlet:
                    elm.close_valve(o, mode='script')

            if inlet:
                self.info('waiting {}s before opening inlet value {}'.format(delay, inlet))
                time.sleep(delay)

                # open inlet
                for i in inlet:
                    elm.open_valve(i, mode='script')

        # set the passed in event
        evt.set()
        # delay for eq time
        self.info('equilibrating for {}sec'.format(eqtime))
        time.sleep(eqtime)
        if self._alive:
            self.heading('Equilibration Finished')
            if elm and inlet and close_inlet:
                for i in inlet:
                    elm.close_valve(i, mode='script')

            if do_post_equilibration:
                self.do_post_equilibration()

            if self.overlap_evt:
                self.debug('setting overlap event. next run ok to start extraction')
                self.overlap_evt.set()

    def _update_labels(self):
        if self.plot_panel:
            if self.plot_panel.isotope_graph:
                # update the plot_panel labels
                plots = self.plot_panel.isotope_graph.plots
                n = len(plots)

                for i, det in enumerate(self._active_detectors):
                    if i < n:
                        plots[i].y_axis.title = det.isotope

    def _update_detectors(self):
        for det in self._active_detectors:
            self.arar_age.set_isotope_detector(det)

    def _set_magnet_position(self, pos, detector,
                             dac=False, update_detectors=True,
                             update_labels=True, update_isotopes=True,
                             remove_non_active=True):
        change = False
        ion = self.ion_optics_manager
        if ion is not None:
            change = ion.position(pos, detector, dac, update_isotopes=update_isotopes)

        if update_labels:
            self._update_labels()
        if update_detectors:
            self._update_detectors()
        if remove_non_active:
            # remove non active isotopes
            for iso in self.arar_age.isotopes.keys():
                det = next((di for di in self._active_detectors if di.isotope == iso), None)
                if det is None:
                    self.arar_age.isotopes.pop(iso)

        if self.plot_panel:
            self.plot_panel.analysis_view.load(self)
            self.plot_panel.analysis_view.refresh_needed = True

        return change

    def _get_data_generator(self):
        def gen():
            cnt = 0
            fcnt = 3
            spec = self.spectrometer_manager.spectrometer
            while 1:
                k, s = spec.get_intensities(tagged=True)
                if not k:
                    cnt += 1
                    self.info('Failed getting intensity from mass spectrometer {}/{}'.format(cnt, fcnt), color='red')
                    if cnt >= fcnt:
                        self.info('Canceling Run. Failed getting intensity from mass spectrometer',
                                  color='red')

                        # do we need to cancel the experiment or will the subsequent pre run
                        # checks sufficient to catch spectrometer communication errors.
                        self.cancel_run(state='failed')
                else:
                    # reset the counter
                    cnt = 0

                    yield k, s

        return gen()

    def _whiff(self, ncounts, conditionals, starttime, starttime_offset, series, fit_series):
        """
        conditionals: list of dicts
        """
        for ci in conditionals:
            if ci.get('start') is None:
                ci['start'] = ncounts

        conds = [conditional_from_dict(ci, ActionConditional) for ci in conditionals]
        self.arar_age.conditional_modifier = 'whiff'
        self.collector.set_temporary_conditionals(conds)
        self.py_data_collection(None, ncounts, starttime, starttime_offset, series, fit_series, group='whiff')
        self.collector.clear_temporary_conditionals()
        self.arar_age.conditional_modifier = None

        result = self.collector.measurement_result
        # self.persister.whiff_result = result
        self._persister_action('trait_set', whiff_result=result)
        self.debug('WHIFF Result={}'.format(result))
        return result

    def _peak_hop(self, ncycles, ncounts, hops, grpname, data_writer,
                  starttime, starttime_offset, series,
                  check_conditionals):
        """
            ncycles: int
            hops: list of tuples

                hop = 'Isotope:Det[,Isotope:Det,...]', Count, Settling Time(s)

                ex.
                hop = 'Ar40:H1,Ar36:CDD', 10, 1
        """
        self.peak_hop_collector.trait_set(ncycles=ncycles,
                                          parent=self)

        self.peak_hop_collector.set_hops(hops)

        if self.experiment_executor:
            sc = self.experiment_executor.signal_color
        else:
            sc = 'red'

        return self._measure(grpname,
                             data_writer,
                             ncounts,
                             starttime, starttime_offset,
                             series, check_conditionals, sc)

    def _sniff(self, ncounts, starttime, starttime_offset, series):
        self.debug('py_sniff')

        if not self._alive:
            return
        p = self.plot_panel
        if p:
            p._ncounts = ncounts
            p.is_baseline = False
            p.isotope_graph.set_x_limits(min_=0, max_=1, plotid=0)

        gn = 'sniff'

        self.persister.build_tables(gn, self._active_detectors)
        # mem_log('build tables')

        check_conditionals = False
        writer = self.persister.get_data_writer(gn)

        if self.experiment_executor:
            sc = self.experiment_executor.sniff_color
        else:
            sc = 'black'

        result = self._measure(gn,
                               writer,
                               ncounts, starttime, starttime_offset,
                               series,
                               check_conditionals, sc)

        return result

    def _measure(self, grpname, data_writer,
                 ncounts, starttime, starttime_offset,
                 series, check_conditionals, color, script=None):

        if script is None:
            script = self.measurement_script

        # mem_log('pre measure')
        if not self.spectrometer_manager:
            self.warning('no spectrometer manager')
            return True

        self.info('measuring {}. ncounts={}'.format(grpname, ncounts),
                  color=MEASUREMENT_COLOR)

        get_data = self._get_data_generator()
        debug = globalv.experiment_debug

        if debug:
            period = 1
        else:
            period = self._integration_seconds

        m = self.collector

        m.trait_set(
            console_display=self.experiment_executor.console_display,
            automated_run=weakref.ref(self)(),
            measurement_script=script,
            detectors=self._active_detectors,
            collection_kind=grpname,
            series_idx=series,
            check_conditionals=check_conditionals,
            ncounts=ncounts,
            period_ms=period * 1000,
            data_generator=get_data,
            data_writer=data_writer,
            starttime=starttime,
            refresh_age=self.spec.analysis_type in ('unknown', 'cocktail'))

        if self.plot_panel:
            self.plot_panel._ncounts = ncounts
            self.plot_panel.total_counts += ncounts
            from pychron.core.ui.gui import invoke_in_main_thread

            invoke_in_main_thread(self._setup_isotope_graph, starttime_offset, color, grpname)

        with self.persister.writer_ctx():
            m.measure()

        # mem_log('post measure')
        if m.terminated:
            self.debug('measurement terminated')
            self.cancel_run()

        return not m.canceled

    #
    def _setup_isotope_graph(self, starttime_offset, color, grpname):
        """
            execute in main thread is necessary.
            set the graph limits and construct the necessary series
            set 0-count fits

        """

        graph = self.plot_panel.isotope_graph
        # update limits
        mi, ma = graph.get_x_limits()

        max_ = ma
        min_ = mi
        tc = self.plot_panel.total_counts
        if tc > ma or ma == Inf:
            max_ = tc * 1.1

        if starttime_offset > mi:
            min_ = -starttime_offset

        graph.set_x_limits(min_=min_, max_=max_)

        series = self.collector.series_idx

        regressing = False
        for k, iso in self.arar_age.isotopes.iteritems():
            idx = graph.get_plotid_by_ytitle(k)
            # print 'ff', k, iso.name, idx
            if idx is not None:
                try:
                    graph.series[idx][series]
                except IndexError, e:
                    fit = None if grpname == 'sniff' else iso.get_fit(0)
                    regressing = fit or regressing
                    graph.new_series(marker='circle',
                                     color=color,
                                     type='scatter',
                                     marker_size=1.25,
                                     fit=fit,
                                     plotid=idx,
                                     add_inspector=False,
                                     add_tools=False)

        scnt, fcnt = (2, 1) if regressing else (1, 0)
        self.measurement_script.increment_series_counts(scnt, fcnt)

        return graph

    def _wait_for(self, predicate, msg):
        st = time.time()
        i = 0
        while self._alive:
            time.sleep(1.0)
            et = time.time() - st
            if predicate(et):
                break

            if i % 5 == 0:
                self.debug(msg(et))
                i = 0
            i += 1

    def _wait_for_min_ms_pumptime(self):
        overlap, mp = self.spec.overlap

        pt = self.experiment_executor.min_ms_pumptime
        if not overlap:
            self.debug('no overlap. not waiting for min ms pumptime')
            return

        if self.is_first:
            self.debug('this is the first run. not waiting for min ms pumptime')
            return

        if not mp:
            self.debug('using default min ms pumptime={}'.format(pt))
            mp = pt

        # ensure mim mass spectrometer pump time
        # wait until pumping started
        self.debug('wait for mass spec pump out to start')
        self._wait_for(lambda x: not self.experiment_executor.ms_pumptime_start is None,
                       msg=lambda x: 'waiting for mass spec pumptime to start {:0.2f}'.format(x))
        self.debug('mass spec pump out to started')

        # wait for min pump time
        pred = lambda x: self.elapsed_ms_pumptime > mp
        msg = lambda x: 'waiting for min mass spec pumptime {}, elapse={:0.2f}'.format(mp, x)
        self._wait_for(pred, msg)
        self.debug('min pumptime elapsed {} {}'.format(mp, self.elapsed_ms_pumptime))

    # ===============================================================================
    # scripts
    # ===============================================================================
    def _load_script(self, name):
        script = None
        sname = getattr(self.script_info, '{}_script_name'.format(name))
        if sname and sname != NULL_STR:
            sname = self._make_script_name(sname)
            skey = '{}{}'.format(name, sname)
            if skey in SCRIPTS:
                script = SCRIPTS[skey]
                if script.check_for_modifications() or self.is_alive():
                    self.debug('script {} modified/overlapping. reloading'.format(sname))
                    script = self._bootstrap_script(sname, name)
            else:
                script = self._bootstrap_script(sname, name)

        return script

    def _bootstrap_script(self, fname, name):
        global SCRIPTS
        global WARNED_SCRIPTS

        def warn(fn, e):
            self.spec.executable = False

            if not fn in WARNED_SCRIPTS:
                WARNED_SCRIPTS.append(fn)
                self.warning_dialog('Invalid Script {}\n{}'.format(fn, e))

        self.debug('loading script "{}"'.format(fname))
        func = getattr(self, '_{}_script_factory'.format(name))
        s = func()
        valid = True

        if s and os.path.isfile(s.filename):
            if s.bootstrap():
                self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%%% setting default context for {}'.format(fname))
                s.set_default_context()
        else:
            valid = False
            fname = s.filename if s else fname
            e = 'Not a file'
            warn(fname, e)

        if valid:
            SCRIPTS[fname] = s
        return s

    def _measurement_script_factory(self):
        from pychron.pyscripts.measurement_pyscript import MeasurementPyScript

        sname = self.script_info.measurement_script_name
        root = paths.measurement_dir
        sname = self._make_script_name(sname)

        ms = MeasurementPyScript(root=root,
                                 name=sname,
                                 runner=self.runner)
        return ms

    def _extraction_script_factory(self, klass=None):
        root = paths.extraction_dir
        return self._ext_factory(root, self.script_info.extraction_script_name,
                                 klass=klass)

    def _post_measurement_script_factory(self):
        root = paths.post_measurement_dir
        return self._ext_factory(root, self.script_info.post_measurement_script_name)

    def _post_equilibration_script_factory(self):
        root = paths.post_equilibration_dir
        return self._ext_factory(root, self.script_info.post_equilibration_script_name)

    def _ext_factory(self, root, file_name, klass=None):
        file_name = self._make_script_name(file_name)
        if os.path.isfile(os.path.join(root, file_name)):
            if klass is None:
                from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript

                klass = ExtractionPyScript

            obj = klass(
                root=root,
                name=file_name,
                runner=self.runner)

            return obj

    def _make_script_name(self, name):
        # name = '{}_{}'.format(self.spec.mass_spectrometer.lower(), name)
        return add_extension(name, '.py')

    def _setup_context(self, script):
        """
            setup_context to expose variables to the pyscript
        """
        ctx = self.spec.make_script_context()
        script.setup_context(is_last=self.is_last, **ctx)

    def _get_yaml_parameter(self, script, key, default):
        if not script:
            return default

        m = ast.parse(script.text)
        docstr = ast.get_docstring(m)
        if docstr:
            docstr = docstr.strip()
            # self.debug('{} {} metadata\n{}'.format(script.name, key, docstr))
            try:
                params = yaml.load(docstr)
                return params[key]
            except KeyError:
                self.warning('No value "{}" in metadata'.format(key))
            except TypeError:
                self.warning('Invalid yaml docstring in "{}". Could not retrieve "{}"'.format(script.name, key))
        else:
            self.debug('No metadata section in "{}". Using default "{}" value for "{}"'.format(script.name,
                                                                                               default, key))

        return default

    def _get_runid(self):
        return self.spec.runid
        # return make_runid(self.spec.labnumber,
        # self.spec.aliquot,
        # self.spec.step)

    def _get_collector(self):
        c = self.peak_hop_collector if self.is_peak_hop else self.multi_collector
        return c

    def _assemble_extraction_blob(self):
        _names, txt = self._assemble_script_blob(kinds=('extraction', 'post_equilibration', 'post_measurement'))
        return txt

    def _assemble_script_blob(self, kinds=None):
        if kinds is None:
            kinds = 'extraction', 'measurement', 'post_equilibration', 'post_measurement'
        okinds = []
        bs = []
        for s in kinds:
            sc = getattr(self, '{}_script'.format(s))
            if sc is not None:
                bs.append((sc.name, sc.toblob()))
                okinds.append(s)

        return assemble_script_blob(bs, kinds=okinds)

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _state_changed(self, old, new):
        self.debug('state changed from {} to {}'.format(old, new))
        if self.spec:
            self.spec.state = self.state

    def _runner_changed(self, new):
        self.debug('Runner runner:{}'.format(new))
        for s in ['measurement', 'extraction', 'post_equilibration', 'post_measurement']:
            sc = getattr(self, '{}_script'.format(s))
            if sc is not None:
                setattr(sc, 'runner', new)

    # ===============================================================================
    # property get/set
    # ===============================================================================
    @property
    def elapsed_ms_pumptime(self):
        return time.time() - self.experiment_executor.ms_pumptime_start

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _measurement_script_default(self):
        return self._load_script('measurement')

    def _post_measurement_script_default(self):
        return self._load_script('post_measurement')

    def _post_equilibration_script_default(self):
        return self._load_script('post_equilibration')

    def _extraction_script_default(self):
        return self._load_script('extraction')

    #
    def _peak_hop_collector_default(self):
        from pychron.experiment.automated_run.peak_hop_collector import PeakHopCollector

        c = PeakHopCollector()
        c.console_bind_preferences('pychron.experiment')
        return c

    def _multi_collector_default(self):
        from pychron.experiment.automated_run.multi_collector import MultiCollector

        c = MultiCollector()
        c.console_bind_preferences('pychron.experiment')
        return c

# ============= EOF =============================================
