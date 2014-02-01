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
from itertools import groupby
from traits.api import Any, Str, List, Property, \
    Event, Instance, Bool, HasTraits, Float
#============= standard library imports ========================
import os
import re
import time
import ast
import yaml
from threading import Thread, Event as TEvent
from uncertainties import ufloat
from numpy import Inf
# from memory_profiler import profile
import weakref
#============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.experiment.automated_run.peak_hop_collector import PeakHopCollector, parse_hops
from pychron.experiment.automated_run.persistence import AutomatedRunPersister
from pychron.experiment.automated_run.syn_extraction import SynExtractionCollector
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.processing.analyses.view.automated_run_view import AutomatedRunAnalysisView
from pychron.pyscripts.measurement_pyscript import MeasurementPyScript
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
from pychron.experiment.plot_panel import PlotPanel
from pychron.experiment.utilities.identifier import convert_identifier, \
    make_runid, get_analysis_type, convert_extract_device
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR, MEASUREMENT_COLOR, \
    EXTRACTION_COLOR, SCRIPT_KEYS
from pychron.experiment.automated_run.condition import TruncationCondition, \
    ActionCondition, TerminationCondition
from pychron.processing.arar_age import ArArAge
from pychron.processing.export.export_spec import assemble_script_blob
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.codetools.memory_usage import mem_log
from pychron.experiment.automated_run.multi_collector import MultiCollector

DEBUG = False

"""
    @todo
    need to handle different integration times

    change total_counts to total_seconds
    convert counts to seconds
        total_seconds += ncounts * self._integration_seconds
"""


class ScriptInfo(HasTraits):
    measurement_script_name = Str
    extraction_script_name = Str
    post_measurement_script_name = Str
    post_equilibration_script_name = Str


SCRIPTS = {}
WARNED_SCRIPTS = []


class AutomatedRun(Loggable):
    spectrometer_manager = Any
    extraction_line_manager = Any
    experiment_executor = Any
    ion_optics_manager = Any

    multi_collector = Instance(MultiCollector, ())
    peak_hop_collector = Instance(PeakHopCollector, ())
    persister = Instance(AutomatedRunPersister, ())
    collector = Property

    script_info = Instance(ScriptInfo, ())

    runner = Any
    monitor = Any
    plot_panel = Any
    arar_age = Instance(ArArAge)

    spec = Any
    runid = Property
    uuid = Str
    extract_device = Str
    analysis_type = Property
    user_defined_aliquot = Bool(False)
    fits = List
    eqtime = Float

    use_syn_extraction = Bool(False)

    is_last = Bool(False)
    is_peak_hop = Bool(False)

    truncated = Bool
    state = Str('not run')
    measuring = Bool(False)
    dirty = Bool(False)
    update = Event

    measurement_script = Instance(MeasurementPyScript)
    post_measurement_script = Instance(ExtractionPyScript)
    post_equilibration_script = Instance(ExtractionPyScript)
    extraction_script = Instance(ExtractionPyScript)

    termination_conditions = List
    truncation_conditions = List
    action_conditions = List

    peak_center = None
    coincidence_scan = None
    info_color = None

    _active_detectors = List
    _peak_center_detectors = List
    _loaded = False
    _measured = False
    _alive = False
    _truncate_signal = Bool
    _equilibration_done = False
    _current_data_frame = None
    _integration_seconds = Float(1.0)


    #===============================================================================
    # pyscript interface
    #===============================================================================
    def py_set_integration_time(self, v):
        spectrometer = self.spectrometer_manager
        nv = spectrometer.set_integration_time(v, force=True)
        self._integration_seconds = nv

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

        fits = dict([f.split(':') for f in fits])
        for k, iso in isotopes.iteritems():
            if k in fits:
                iso.set_fit_blocks(fits[k])
            else:
                self.warning('Invalid fit "{}". '
                             'check the measurement script "{}"'.format(k,self.measurement_script.name))

    def py_set_baseline_fits(self, fits):
        isotopes = self.arar_age.isotopes
        if len(fits) == 1:
            fs = []
            for di in self._active_detectors:
                fs.append('{}:{}'.format(di.name, fits[0]))
            fits = fs

        fits = dict([f.split(':') for f in fits])
        for k, iso in isotopes.iteritems():
            iso.baseline.set_fit_blocks(fits[iso.detector])

    def py_get_spectrometer_parameter(self, name):
        self.info('getting spectrometer parameter {}'.format(name))
        if self.spectrometer_manager:
            return self.spectrometer_manager.spectrometer.get_parameter(name)

    def py_set_spectrometer_parameter(self, name, v):
        self.info('setting spectrometer parameter {} {}'.format(name, v))
        if self.spectrometer_manager:
            self.spectrometer_manager.spectrometer.set_parameter(name, v)

    def py_data_collection(self, obj, ncounts, starttime, starttime_offset, series=0):
        if not self._alive:
            return

        if self.plot_panel:
            self.plot_panel.is_baseline = False

        gn = 'signal'

        self.persister.build_tables(gn, self._active_detectors)

        self._add_truncate_condition()

        self.multi_collector.is_baseline = False
        if self.experiment_executor:
            sc=self.experiment_executor.signal_color
        else:
            sc='red'

        check_conditions= obj==self.measurement_script

        result = self._measure(gn,
                               self.persister.get_data_writer(gn),
                               ncounts, starttime, starttime_offset,
                               series,
                               check_conditions, sc, obj)
        return result

    def py_equilibration(self, eqtime=None, inlet=None, outlet=None,
                         do_post_equilibration=True,
                         delay=None):
        evt = TEvent()
        if not self._alive:
            evt.set()
            return evt

        self.info('====== Equilibration Started ======')
        t = Thread(name='equilibration', target=self._equilibrate, args=(evt,),
                   kwargs=dict(eqtime=eqtime,
                               inlet=inlet,
                               outlet=outlet,
                               delay=delay,
                               do_post_equilibration=do_post_equilibration))
        t.start()

        return evt

    def py_sniff(self, ncounts, starttime, starttime_offset, series=0):
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
        mem_log('build tables')

        check_conditions = False
        writer = self.persister.get_data_writer(gn)

        if self.experiment_executor:
            sc = self.experiment_executor.sniff_color
        else:
            sc = 'black'

        result = self._measure(gn,
                               writer,
                               ncounts, starttime, starttime_offset,
                               series,
                               check_conditions, sc)

        return result

    def py_baselines(self, ncounts, starttime, starttime_offset, mass, detector,
                     series=0, settling_time=4):

        if not self._alive:
            return

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

        gn = 'baseline'

        self.persister.build_tables(gn, self._active_detectors)

        self.multi_collector.is_baseline = True
        check_conditions = True

        self.collector.for_peak_hop = self.plot_panel.is_peak_hop

        if self.experiment_executor:
            sc = self.experiment_executor.baseline_color
        else:
            sc = 'green'
        result = self._measure(gn,
                               self.persister.get_data_writer(gn),
                               ncounts, starttime,
                               starttime_offset,
                               series,
                               check_conditions,sc)

        if self.plot_panel:
            bs = dict([(iso.name, iso.baseline.uvalue) for iso in
                       self.arar_age.isotopes.values()])
            self.set_previous_baselines(bs)
        self.multi_collector.is_baseline = False
        return result

    def py_define_hops(self, hopstr):
        """
            set the detector each isotope
            add additional isotopes and associated plots if necessary
        """
        if self.plot_panel is None:
            self.warning('Need to call "define_hops(...)" after "activate_detectors(...)"')
            return

        self.plot_panel.is_peak_hop = True

        key = lambda x: x[0]
        hops = parse_hops(hopstr, ret='iso,det')
        hops = sorted(hops, key=key)
        a = self.arar_age
        g = self.plot_panel.isotope_graph
        for iso, dets in groupby(hops, key=key):
            dets = list(dets)
            add_detector = len(dets) > 1

            plot = g.get_plot_by_ytitle(iso)
            for _, di in dets:
                name = iso
                if iso in a.isotopes:
                    ii = a.isotopes[iso]
                    ii.detector = di
                    a.isotopes.pop(iso)
                else:
                    ii = a.isotope_factory(name=iso, detector=di)
                    pid = g.plots.index(plot)
                    n = len(plot.plots)
                    plot = self.plot_panel.new_plot(add=pid + 1)
                    pid = g.plots.index(plot)
                    for i in range(n):
                        g.new_series(kind='scatter', fit=None, plotid=pid)

                if add_detector:
                    name = '{}{}'.format(name, di)

                a.isotopes[name] = ii
                plot.y_axis.title = name

        self.plot_panel.analysis_view.load(self)

    def py_peak_hop(self, cycles, counts, hops, starttime, starttime_offset,
                    series=0, group='signal'):

        if not self._alive:
            return

        is_baseline = False
        self.peak_hop_collector.is_baseline = is_baseline

        if self.plot_panel:
            self.plot_panel.trait_set(is_baseline=is_baseline,
                                      _ncycles=cycles,
                                      hops=hops)

        self.persister.save_as_peak_hop = True
        self.is_peak_hop = True

        self.persister.build_peak_hop_tables(group, hops)
        writer = self.persister.get_data_writer(group)

        check_conditions = True
        self._add_truncate_condition()

        ret = self._peak_hop(cycles, counts, hops, group, writer,
                             starttime, starttime_offset, series,
                             check_conditions)

        self.is_peak_hop = False
        return ret

    def py_peak_center(self, detector=None, save=True, **kw):
        if not self._alive:
            return
        ion = self.ion_optics_manager

        if ion is not None:
            if not self.plot_panel:
                p = self._new_plot_panel(self.plot_panel, stack_order='top_to_bottom')
                self.plot_panel = p

            self.debug('peak center started')

            ad = [di.name for di in self._peak_center_detectors
                  if di.name != detector]

            pc = ion.setup_peak_center(detector=[detector] + ad,
                                       plot_panel=self.plot_panel,
                                       **kw)
            self.peak_center = pc

            ion.do_peak_center(new_thread=False, save=save)

            if pc.result:
                dm = self.persister.data_manager

                with dm.open_file(self._current_data_frame):
                    tab = dm.new_table('/', 'peak_center')
                    xs, ys = pc.graph.get_data(), pc.graph.get_data(axis=1)

                    for xi, yi in zip(xs, ys):
                        nrow = tab.row
                        nrow['time'] = xi
                        nrow['value'] = yi
                        nrow.append()

                    xs, ys, _mx, _my = pc.result
                    attrs = tab.attrs
                    attrs.low_dac = xs[0]
                    attrs.center_dac = xs[1]
                    attrs.high_dac = xs[2]

                    attrs.low_signal = ys[0]
                    attrs.center_signal = ys[1]
                    attrs.high_signal = ys[2]
                    tab.flush()

    def py_coincidence_scan(self):
        sm = self.spectrometer_manager
        obj, t = sm.do_coincidence_scan()
        self.coincidence_scan = obj
        t.join()

    #===============================================================================
    # conditions
    #===============================================================================
    def py_add_termination(self, attr, comp, start_count, frequency):
        """
            attr must be an attribute of arar_age
        """
        self.termination_conditions.append(TerminationCondition(attr, comp,
                                                                start_count,
                                                                frequency))

    def py_add_truncation(self, attr, comp, start_count, frequency,
                          abbreviated_count_ratio):
        """
            attr must be an attribute of arar_age
        """
        self.info('adding truncation {} {} {}'.format(attr, comp, start_count))

        if not self.arar_age.has_attr(attr):
            self.warning('invalid truncation attribute "{}"'.format(attr))
        else:
            self.truncation_conditions.append(TruncationCondition(attr, comp,
                                                                  start_count,
                                                                  frequency,
                                                                  abbreviated_count_ratio=abbreviated_count_ratio))

    def py_add_action(self, attr, comp, start_count, frequency, action, resume):
        """
            attr must be an attribute of arar_age
        """
        self.action_conditions.append(ActionCondition(attr, comp,
                                                      start_count,
                                                      frequency,
                                                      action=action,
                                                      resume=resume))

    def py_clear_conditions(self):
        self.py_clear_terminations()
        self.py_clear_truncations()
        self.py_clear_actions()

    def py_clear_terminations(self):
        self.termination_conditions = []

    def py_clear_truncations(self):
        self.truncation_conditions = []

    def py_clear_actions(self):
        self.action_conditions = []

    #===============================================================================
    # run termination
    #===============================================================================
    def cancel_run(self, state='canceled'):
        """
            terminate the measurement script immediately

            do post termination
                post_eq and post_meas
            don't save run

        """
        #self.multi_collector.canceled = True
        self.collector.canceled = True

        #        self.aliquot='##'
        self.persister.save_enabled = False
        for s in ('extraction', 'measurement'):
            script = getattr(self, '{}_script'.format(s))
            if script is not None:
                script.cancel()

        self.debug('peak center {}'.format(self.peak_center))
        if self.peak_center:
            self.peak_center.cancel()

        self.do_post_termination()

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

            #             self._truncate_signal = True
            #self.multi_collector.set_truncated()
            self.collector.set_truncated()
            self.truncated = True
            self.state = 'truncated'
            #===============================================================================
            #
            #===============================================================================

    def teardown(self):
    #         gc.collect()
    #         return

    #         if self.plot_panel:
    #             self.plot_panel.automated_run = None
    #         self.plot_panel = None
    #             self.plot_panel.arar_age = None
    #             self.plot_panel.info_func = None

    #         if self.monitor:
    #             self.monitor.automated_run = None
    #
        if self.measurement_script:
            self.measurement_script.automated_run = None

        self.py_clear_conditions()

    def finish(self):

        if self.monitor:
            self.monitor.stop()

        if self.state not in ('not run', 'canceled', 'success', 'truncated'):
            self.state = 'failed'

        self.stop()

    def stop(self):
        self._alive = False
        self.collector.stop()

    def wait(self, t, msg=''):
        if self.experiment_executor:
            self.experiment_executor.wait(t, msg)
        else:
            time.sleep(t / 10.)

    def info(self, msg, color=None, *args, **kw):
        super(AutomatedRun, self).info(msg, *args, **kw)
        if self.experiment_executor:
            if color is None:
                color = self.info_color

            if color is None:
                color = 'light green'

            self.experiment_executor.info(msg, color=color, log=False)

    def isAlive(self):
        return self._alive

    def get_detector(self, det):
        return self.spectrometer_manager.spectrometer.get_detector(det)

    def set_magnet_position(self, *args, **kw):
        self._set_magnet_position(*args, **kw)

    def set_deflection(self, det, defl):
        self.py_set_spectrometer_parameter('SetDeflection', '{},{}'.format(det, defl))

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

    def wait_for_overlap(self):
        '''
            by default overlap_evt is set 
            after equilibration finished
        '''
        self.info('waiting for overlap signal')
        evt = self.overlap_evt
        evt.wait()

        overlap = self.spec.overlap
        self.info('starting overlap delay {}'.format(overlap))
        starttime = time.time()
        while self._alive:
            if time.time() - starttime > overlap:
                break
            time.sleep(1.0)

    def get_previous_blanks(self):
        blanks = None
        if self.experiment_executor:
            blanks = self.experiment_executor.get_prev_blanks()

        if not blanks:
            blanks = dict(Ar40=ufloat(0, 0),
                          Ar39=ufloat(0, 0),
                          Ar38=ufloat(0, 0),
                          Ar37=ufloat(0, 0),
                          Ar36=ufloat(0, 0))

        return blanks

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

    def _start(self):
    #         self.db.reset()

        if self._use_arar_age():
            if self.arar_age is None:
            #             # load arar_age object for age calculation
                self.arar_age = ArArAge()

            es = self.extraction_script
            if es is not None:
                # get senstivity multiplier from extraction script
                v = self._get_yaml_parameter(es, 'sensitivity_multiplier', default=1)
                self.arar_age.sensitivity_multiplier = v

            ln = self.spec.labnumber
            ln = convert_identifier(ln)
            self.persister.datahub.load_analysis_backend(ln, self.arar_age)

        self.info('Start automated run {}'.format(self.runid))

        self.measuring = False
        #             self.update = True
        self.truncated = False

        self.overlap_evt = TEvent()
        self._alive = True

        if self.plot_panel:
            self.plot_panel.total_counts = 0
            self.plot_panel.is_peak_hop = False
            self.plot_panel.is_baseline = False

        self.multi_collector.canceled = False
        self.multi_collector.is_baseline = False
        self.multi_collector.for_peak_hop = False

        self._equilibration_done = False
        self.refresh_scripts()

        # setup the scripts
        if self.measurement_script:
            self.measurement_script.reset(weakref.ref(self)())
            #            self.debug('XXXXXXXXXXXXXXXXXXXXXXXXX Setting measurement script is_last {}'.format(self.is_last))
        #            self.measurement_script.setup_context(is_last=self.is_last)

        for si in ('extraction', 'post_measurement', 'post_equilibration'):
            script = getattr(self, '{}_script'.format(si))
            if script:
                self._setup_context(script)

        #load extraction metadata
        self.eqtime = self._get_extraction_parameter('eqtime', 15)

        #setup persister. mirror a few of AutomatedRunsAttributes
        self.setup_persister()

        return True

    #===============================================================================
    # setup
    #===============================================================================
    def setup_persister(self):
        sens = self._get_extraction_parameter('sensitivity_multiplier', default=1)

        #setup persister. mirror a few of AutomatedRunsAttributes
        script_name, script_blob = self._assemble_script_blob()
        eqn, eqb = '', ''
        pb = {}
        if self.experiment_executor:
            eqn = self.experiment_executor.experiment_queue.name
            eqb = self.experiment_executor.experiment_blob()
            pb = self.experiment_executor.get_prev_blanks()

        ext_name, ext_blob = '', ''
        if self.extraction_script:
            ext_name = self.extraction_script.name
            ext_blob = self._assemble_extraction_blob()

        ms_name, ms_blob = '', ''
        if self.measurement_script:
            ms_name = self.measurement_script.name
            ms_blob = self.measurement_script.toblob()

        self.persister.trait_set(uuid=self.uuid,
                                 runid=self.runid,
                                 save_as_peak_hop=False,
                                 run_spec=self.spec,
                                 arar_age=self.arar_age,
                                 positions=self.get_position_list(),
                                 sensitivity_multiplier=sens,
                                 experiment_queue_name=eqn,
                                 experiment_queue_blob=eqb,
                                 extraction_name=ext_name,
                                 extraction_blob=ext_blob,
                                 measurement_name=ms_name,
                                 measurement_blob=ms_blob,
                                 previous_blanks=pb,
                                 runscript_name=script_name,
                                 runscript_blob=script_blob)

    #===============================================================================
    # doers
    #===============================================================================
    def start_extraction(self):
        return self._start_script('extraction')

    def start_measurement(self):
        return self._start_script('measurement')

    def do_extraction(self):
        self.debug('do extraction')

        self.persister.pre_extraction_save()

        self.info_color = EXTRACTION_COLOR
        msg = 'Extraction Started {}'.format(self.extraction_script.name)
        self.info('======= {} ======='.format(msg))
        self.state = 'extraction'

        self.debug('DO EXTRACTION {}'.format(self.runner))
        self.extraction_script.runner = self.runner
        self.extraction_script.manager = self.experiment_executor
        self.extraction_script.run_identifier = self.runid

        syn_extractor=None
        if self.extraction_script.syntax_ok(warn=False):
            if self.use_syn_extraction:
                p=os.path.join(paths.scripts_dir, 'syn_extraction',self.spec.syn_extraction)
                p=add_extension(p,'.yaml')

                if os.path.isfile(p):
                    dur=self.extraction_script.calculate_estimated_duration(force=True)
                    syn_extractor=SynExtractionCollector(arun=weakref.ref(self)(),
                                                         path=p,
                                                         extraction_duration=dur)
                    syn_extractor.start()
                else:
                    self.warning('Cannot start syn extraction collection. Configuration file does not exist. {}'.format(p))
        else:
            self.warning('Invalid script syntax for "{}"'.format(self.extraction_script.name))
            return
        if self.extraction_script.execute():
            if syn_extractor:
                syn_extractor.stop()

            #report the extraction results
            r = self.extraction_script.output_achieved()
            for ri in r:
                self.info(ri)

            self.persister.post_extraction_save()
            self.info('======== Extraction Finished ========')
            self.info_color = None
            return True
        else:
            if syn_extractor:
                syn_extractor.stop()

            self.do_post_equilibration()
            self.do_post_measurement()
            self.finish()

            self.info('======== Extraction Finished unsuccessfully ========', color='red')
            self.info_color = None
            return False

    def do_measurement(self, script=None, use_post_on_fail=True):
        self.debug('do measurement')
        if not self._alive:
            self.warning('run is not alive')
            return

        if script is None:
            script=self.measurement_script

        if script is None:
            self.warning('no measurement script')
            return

        script.trait_set(runner=self.runner,
                         manager=self.experiment_executor)

        # use a measurement_script to explicitly define
        # measurement sequence
        self.info_color = MEASUREMENT_COLOR
        msg = 'Measurement Started {}'.format(script.name)
        self.info('======== {} ========'.format(msg))
        self.state = 'measurement'

        self.persister.pre_measurement_save()

        self.measuring = True
        self.persister.save_enabled = True

        if script.execute():
            mem_log('post measurement execute')
            self.info('======== Measurement Finished ========')
            self.measuring = False
            self.info_color = None

            self._measured = True
            return self.post_measurement_save()

        else:
            if use_post_on_fail:
                self.do_post_equilibration()
                self.do_post_measurement()
            self.finish()

            self.info('======== Measurement Finished unsuccessfully ========', color='red')
            self.measuring = False
            self.info_color = None
            return False

    def do_post_measurement(self, script=None):
        if script is None:
            script=self.post_measurement_script

        if not script:
            return True

        if not self._alive:
            return

        msg = 'Post Measurement Started {}'.format(script.name)
        self.info('======== {} ========'.format(msg))
        #        self.state = 'extraction'
        script.runner = self.runner
        script.manager = self.experiment_executor

        if script.execute():
            self.info('======== Post Measurement Finished ========')
            return True
        else:
            self.info('======== Post Measurement Finished unsuccessfully ========')
            return False

    def do_post_equilibration(self):
        if self._equilibration_done:
            return

        self._equilibration_done = True

        if not self._alive:
            return

        if self.post_equilibration_script is None:
            return
        msg = 'Post Equilibration Started {}'.format(self.post_equilibration_script.name)
        self.info('======== {} ========'.format(msg))
        self.post_equilibration_script.runner = self.runner
        self.post_equilibration_script.manager = self.experiment_executor

        #         self.post_equilibration_script.syntax_checked = True
        if self.post_equilibration_script.execute():
            self.info('======== Post Equilibration Finished ========')
        else:
            self.info('======== Post Equilibration Finished unsuccessfully ========')

    def do_post_termination(self):
        oex = self.experiment_executor.executable
        self.experiment_executor.executable = False
        self.info('========= Post Termination Started ========')
        self.do_post_equilibration()
        self.do_post_measurement()

        self.stop()

        self.info('========= Post Termination Finished ========')
        self.experiment_executor.executable = oex

    #===============================================================================
    # utilities
    #===============================================================================
    def assemble_report(self):
        signal_string = ''
        signals = self.get_baseline_corrected_signals()
        if signals:
            for ai in self._active_detectors:
                det = ai.name
                iso = ai.isotope
                v = signals[iso]
                signal_string += '{} {} {}\n'.format(det, iso, v)

                #        signal_string = '\n'.join(['{} {}'.format(k, v) for k, v in self.signals.iteritems()])
        age = ''
        if self.arar_age:
            age = self.arar_age.age
        age_string = 'age={}'.format(age)

        return '''runid={} timestamp={} {}
anaylsis_type={}        
#===============================================================================
# signals
#===============================================================================
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

    def get_position_list(self):
        return self._make_iterable(self.spec.position)

    def setup_context(self, *args, **kw):
        self._setup_context(*args, **kw)

    #===============================================================================
    # private
    #===============================================================================
    #     def _plot_panel_closed(self):
    #         if self.measuring:
    #             from pychron.core.ui.thread import Thread as mThread
    #             self._term_thread = mThread(target=self.cancel_run)
    #             self._term_thread.start()
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
        #             p.clear_displays()
            p.isotope_graph.clear_plots()

        p.show_isotope_graph()

        # for iso in self.arar_age.isotopes:
        self.arar_age.clear_isotopes()
        self.arar_age.clear_error_components()
        self.arar_age.clear_blanks()

        cb = False
        if (not self.spec.analysis_type.startswith('blank') \
                and not self.spec.analysis_type.startswith('background')):

            cb = True
            #blanks=None
            #if self.experiment_executor:
            #    blanks = self.experiment_executor.get_prev_blanks()
            #
            #if not blanks:
            #    blanks = dict(Ar40=(0, 0), Ar39=(0, 0), Ar38=(0, 0), Ar37=(0, 0), Ar36=(0, 0))
            blanks = self.get_previous_blanks()

            for iso, v in blanks.iteritems():
                self.arar_age.set_blank(iso, v)

        for d in self._active_detectors:
            self.arar_age.set_isotope(d.isotope, (0, 0),
                                      detector=d.name,
                                      correct_for_blank=cb)

        self.arar_age.clear_baselines()
        #baselines=None
        #if self.experiment_executor:
        #    baselines = self.experiment_executor.get_prev_baselines()
        #
        #if not baselines:
        #    baselines = dict(Ar40=(0, 0), Ar39=(0, 0), Ar38=(0, 0), Ar37=(0, 0), Ar36=(0, 0))
        baselines = self.get_previous_baselines()
        for iso, v in baselines.iteritems():
            self.arar_age.set_baseline(iso, v)

        p.analysis_view.load(self)

    def _add_truncate_condition(self):
        t = self.spec.truncate_condition
        self.debug('adding truncate condition {}'.format(t))
        if t:
            p = os.path.join(paths.truncation_dir, add_extension(t, '.yaml'))
            if os.path.isfile(p):
                self.debug('extract truncations from file. {}'.format(p))
                with open(p, 'r') as fp:
                    doc = yaml.load(fp)

                    for c in doc:
                        attr = c['attr']
                        comp = c['comp']
                        start = c['start']
                        freq = c.get('frequency', 1)
                        acr = c.get('abbreviated_count_ratio', 1)
                        self.py_add_truncation(attr, comp, int(start), freq, acr)

            else:
                try:
                    c, start = t.split(',')
                    pat = '<=|>=|[<>=]'
                    attr = re.split(pat, c)[0]
                    # attr, value = re.split(pat, c)
                    # m = re.search(pat, c)
                    # comp = m.group(0)

                    freq = 1
                    acr = 1
                except Exception, e:
                    self.debug('truncate_condition parse failed {} {}'.format(e, t))
                    return

                self.py_add_truncation(attr, c, int(start), freq, acr)



    def _make_iterable(self, pos):
        if '(' in pos and ')' in pos and ',' in pos:
            # interpret as (x,y)
            pos = pos.strip()[1:-1]
            ps = [map(float, pos.split(','))]

        elif ',' in pos:
            # interpert as list of holenumbers
            ps = list(pos.split(','))
        else:
            ps = [pos]

        return ps

    def _get_measurement_parameter(self, key, default=None):
        return self._get_yaml_parameter(self.measurement_script, key, default)

    def _get_extraction_parameter(self, key, default=None):
        return self._get_yaml_parameter(self.extraction_script, key, default)

    def _use_arar_age(self):
    #        return True
        ln = self.spec.labnumber
        return ln not in ('dg', 'pa')

    #        if '-' in ln:
    #            ln = ln.split('-')[0]
    #
    #        return self.spec.analysis_type == 'unknown' or ln in ('c',)

    def _new_plot_panel(self, plot_panel, stack_order='bottom_to_top'):

        title = self.runid
        sample, irradiation = self.spec.sample, self.spec.irradiation
        if sample:
            title = '{}   {}'.format(title, sample)
        if irradiation:
            title = '{}   {}'.format(title, irradiation)

        if plot_panel is None:
            plot_panel = PlotPanel(
                stack_order=stack_order,
                info_func=self.info,
                arar_age=self.arar_age)

        an = AutomatedRunAnalysisView(analysis_type=self.analysis_type,
                                      analysis_id=self.runid)
        an.load(self)

        plot_panel.trait_set(
            plot_title=title,
            analysis_view=an,
            refresh_age=self.analysis_type in ('unknown', 'cocktail'))

        return plot_panel

    def _equilibrate(self, evt, eqtime=15, inlet=None, outlet=None,
                     delay=3,
                     do_post_equilibration=True):

        elm = self.extraction_line_manager
        if elm:
            if outlet:
                # close mass spec ion pump
                elm.close_valve(outlet, mode='script')

            if inlet:
                self.info('waiting {}s before opening inlet value {}'.format(delay, inlet))
                time.sleep(delay)
                # open inlet
                elm.open_valve(inlet, mode='script')

        evt.set()

        # delay for eq time
        self.info('equilibrating for {}sec'.format(eqtime))
        time.sleep(eqtime)
        if self._alive:
            self.info('======== Equilibration Finished ========')
            if elm and inlet:
                elm.close_valve(inlet)

            if do_post_equilibration:
                self.do_post_equilibration()

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

                        # self.arar_age.set_isotope_detector(det)

    def _update_detectors(self):
        for det in self._active_detectors:
            self.arar_age.set_isotope_detector(det)

    def _set_magnet_position(self, pos, detector,
                             dac=False, update_detectors=True,
                             update_labels=True, update_isotopes=True,
                             remove_non_active=True):
        ion = self.ion_optics_manager
        if ion is not None:
            ion.position(pos, detector, dac, update_isotopes=update_isotopes)

        if update_labels:
            self._update_labels()
        if update_detectors:
            self._update_detectors()
        if remove_non_active:
            #remove non active isotopes
            for iso in self.arar_age.isotopes.keys():
                det = next((di for di in self._active_detectors if di.isotope == iso), None)
                if det is None:
                    self.arar_age.isotopes.pop(iso)

        if self.plot_panel:
            self.plot_panel.analysis_view.load(self)
            self.plot_panel.analysis_view.refresh_needed = True

    def _peak_hop(self, ncycles, ncounts, hops, grpname, data_writer,
                  starttime, starttime_offset, series,
                  check_conditions):
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

        #self.peak_hop_collector.stop()
        #ncounts = sum([ci+s for _h, ci, s in hops]) * ncycles
        #ncounts = self.measurement_script.ncounts
        # check_conditions = True
        return self._measure(grpname,
                             data_writer,
                             ncounts,
                             starttime, starttime_offset,
                             series, check_conditions, 'black')

    def _get_data_generator(self):
        def gen():
            spec = self.spectrometer_manager.spectrometer
            while 1:
                v = spec.get_intensities(tagged=True)
                yield v

        return gen()

    def _measure(self, grpname, data_writer,
                 ncounts, starttime, starttime_offset,
                 series, check_conditions, color, script=None):

        if script is None:
            script=self.measurement_script

        mem_log('pre measure')
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
            plot_panel=self.plot_panel,
            arar_age=self.arar_age,
            measurement_script=script,
            detectors=self._active_detectors,
            truncation_conditions=self.truncation_conditions,
            termination_conditions=self.termination_conditions,
            action_conditions=self.action_conditions,

            collection_kind=grpname,
            series_idx=series,
            check_conditions=check_conditions,
            ncounts=ncounts,
            period_ms=period * 1000,
            data_generator=get_data,
            data_writer=data_writer,
            starttime=starttime)

        #m.total_counts += ncounts
        if self.plot_panel:
            self.plot_panel._ncounts = ncounts
            self.plot_panel.total_counts += ncounts
            invoke_in_main_thread(self._setup_isotope_graph, starttime_offset, color)

        # dm = self.persister.data_manager
        with self.persister.writer_ctx():
        # with dm.open_file(self.current_data_frame):
            m.measure()

        mem_log('post measure')
        return True

    def _setup_isotope_graph(self, starttime_offset, color):
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

        # nfs = self.collector.get_fit_block(0, fits)
        series = self.collector.series_idx
        for k, iso in self.arar_age.isotopes.iteritems():
            idx = graph.get_plotid_by_ytitle(k)
            if idx is not None:
                try:
                    graph.series[idx][series]
                except IndexError:
                    graph.new_series(marker='circle',
                                     color=color,
                                     type='scatter',
                                     marker_size=1.25,
                                     fit=iso.get_fit(0),
                                     plotid=idx,
                                     add_inspector=False,
                                     add_tools=False)

        # for pi, (fi, dn) in enumerate(zip(nfs, self._active_detectors)):
        #     #only add if this series doesnt exist for this plot
        #     try:
        #         graph.series[pi][series]
        #     except IndexError:
        #         graph.new_series(marker='circle',
        #                          type='scatter',
        #                          marker_size=1.25,
        #                          fit=fi,
        #                          plotid=pi,
        #                          add_inspector=False,
        #                          add_tools=False)
        return graph

    #===============================================================================
    # save
    #===============================================================================
    #         with dm.new_frame_ctx(path) as frame:
    # save some metadata with the file
    #             attrs = frame.root._v_attrs
    #             attrs['USER'] = self.spec.username
    #             attrs['ANALYSIS_TYPE'] = self.spec.analysis_type
    #             attrs['TIMESTAMP'] = time.time()
    def post_measurement_save(self):
        if self._measured:
            if self.spectrometer_manager:
                self.persister.trait_set(spec_dict=self.spectrometer_manager.make_parameters_dict(),
                                         defl_dict=self.spectrometer_manager.make_deflections_dict(),
                                         active_detectors=self._active_detectors)

            self.persister.post_measurement_save()
            if self.persister.secondary_database_fail:
                if self.experiment_executor:
                    self.experiment_executor.cancel(cancel_run=True,
                                                    msg=self.persister.secondary_database_fail)
            else:
                return True
                #===============================================================================
                # scripts

    #===============================================================================
    def _load_script(self, name):
        script = None
        sname = getattr(self.script_info, '{}_script_name'.format(name))

        if sname and sname != NULL_STR:
            sname = self._make_script_name(sname)
            #            print sname, self.scripts
            if sname in SCRIPTS:
                script = SCRIPTS[sname]
                if script.check_for_modifications():
                    self.debug('script {} modified reloading'.format(sname))
                    script = self._bootstrap_script(sname, name)
            else:
                script = self._bootstrap_script(sname, name)

        return script

    def _bootstrap_script(self, fname, name):
        global SCRIPTS
        global WARNED_SCRIPTS
        #if not self.WARNED_SCRIPTS:
        #    self.WARNED_SCRIPTS = []
        #WARNED_SCRIPTS = self.WARNED_SCRIPTS

        def warn(fn, e):
            # self.invalid_script = True
            # self.executable = False
            self.spec.executable = False

            if not fn in WARNED_SCRIPTS:
                WARNED_SCRIPTS.append(fn)
                #                 e = traceback.format_exc()
                self.warning_dialog('Invalid Script {}\n{}'.format(fn, e))

        self.info('loading script "{}"'.format(fname))
        func = getattr(self, '_{}_script_factory'.format(name))
        s = func()
        valid = True
        if s and os.path.isfile(s.filename):
            if s.bootstrap():
                s.set_default_context()
                # try:
                #     s.test()
                # #                    s.test()
                # # #                    setattr(self, '_{}_script'.format(name), s)
                # except Exception, e:
                #     e = traceback.format_exc()
                #     warn(fname, e)
                #     valid = False
                #                    setattr(self, '_{}_script'.format(name), None)
        else:
            valid = False
            fname = s.filename if s else fname
            e = 'Not a file'
            warn(fname, e)

        # self.valid_scripts[name] = valid
        if valid:
            SCRIPTS[fname] = s
        return s

    def _measurement_script_factory(self):

        sname = self.script_info.measurement_script_name
        root = paths.measurement_dir
        sname = self._make_script_name(sname)

        ms = MeasurementPyScript(root=root,
                                 name=sname,
                                 runner=self.runner)
        #        ms.setup_context(is_last=self.is_last)

        return ms

    def _extraction_script_factory(self, klass=None):
        root = paths.extraction_dir
        #klass = None
        #print 'edivas', self.extract_device
        #if self.extract_device == 'Fusions UV':
        #    klass = UVExtractionPyScript
        #    self.debug('{}'.format(self.extract_device))
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
                klass = ExtractionPyScript

            obj = klass(
                root=root,
                name=file_name,
                runner=self.runner
            )

            return obj

    def _make_script_name(self, name):
        name = '{}_{}'.format(self.spec.mass_spectrometer.lower(), name)
        name = self._add_script_extension(name)
        return name

    def _setup_context(self, script):
        """
            setup_context to expose variables to the pyscript
        """
        spec = self.spec
        hdn = convert_extract_device(spec.extract_device)
        #hdn = spec.extract_device.replace(' ', '_').lower()
        an = spec.analysis_type.split('_')[0]
        script.setup_context(tray=spec.tray,
                             position=self.get_position_list(),
                             disable_between_positions=spec.disable_between_positions,
                             duration=spec.duration,
                             extract_value=spec.extract_value,
                             extract_units=spec.extract_units,
                             cleanup=spec.cleanup,
                             extract_device=hdn,
                             analysis_type=an,
                             ramp_rate=spec.ramp_rate,
                             pattern=spec.pattern,
                             beam_diameter=spec.beam_diameter,
                             ramp_duration=spec.ramp_duration,
                             is_last=self.is_last)

    def _add_script_extension(self, name, ext='.py'):
        return name if name.endswith(ext) else name + ext

    def _get_yaml_parameter(self, script, key, default):
        if not script:
            return default

        m = ast.parse(script.text)
        docstr = ast.get_docstring(m)
        self.debug('{} {} metadata {}'.format(script.name, key, docstr))
        if docstr:
            try:
                params = yaml.load(docstr)
                return params[key]
            except KeyError:
                self.warning('No value "{}" in metadata'.format(key))
            except TypeError:
                self.warning('Invalid yaml docstring in {}. Could not retrieve {}'.format(script.name, key))

        return default

    def refresh_scripts(self):
        for name in SCRIPT_KEYS:
            setattr(self, '{}_script'.format(name), self._load_script(name))

    def _measurement_script_default(self):
        return self._load_script('measurement')

    def _post_measurement_script_default(self):
        return self._load_script('post_measurement')

    def _post_equilibration_script_default(self):
        return self._load_script('post_equilibration')

    def _extraction_script_default(self):
        return self._load_script('extraction')

    def _get_runid(self):
        return make_runid(self.spec.labnumber,
                          self.spec.aliquot,
                          self.spec.step)

    def _get_analysis_type(self):
        return get_analysis_type(self.spec.labnumber)

    def _get_collector(self):
        return self.peak_hop_collector if self.is_peak_hop else self.multi_collector

    def _assemble_extraction_blob(self):
        _names, txt = self._assemble_script_blob(kinds=('extraction', 'post_equilibration', 'post_measurement'))
        return txt

    def _assemble_script_blob(self, kinds=None):
        if kinds is None:
            kinds = 'extraction', 'measurement', 'post_equilibration', 'post_measurement'
        okinds = []
        bs = []
        for s in kinds:  # ('extraction', 'post_equilibration', 'post_measurement'):
            sc = getattr(self, '{}_script'.format(s))
            if sc is not None:
                bs.append((sc.name, sc.toblob()))
                okinds.append(s)

        return assemble_script_blob(bs, kinds=okinds)

    #===============================================================================
    # handlers
    #===============================================================================
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
            #============= EOF =============================================

            # def _time_save(self, func, name, *args, **kw):
            #     st = time.time()
            #     r = func(*args, **kw)
            #     self.debug('save {} time= {:0.3f}'.format(name, time.time() - st))
            #     return r

            # def _is_peak_hop_changed(self, new):
            #     if self.plot_panel:

#         self.debug('Setting is_peak_hop {}'.format(new))
#         self.plot_panel.is_peak_hop = new
#===============================================================================
# defaults
#===============================================================================

#def _multi_collector_default(self):
#    return MultiCollector()



# for kind in ('sniff','signal','baseline'):
#     dbiso = db.add_isotope(analysis, iso.name, det,
#                            kind=kind)
#     if kind in ('sniff', 'baseline'):
#         m=getattr(iso, kind)
#     else:
#         m=iso
#
#     self.debug('saving signal {} xs={}'.format(iso.name, len(m.xs)))
#     data = ''.join([struct.pack('>ff', x, y) for x, y in zip(m.xs, m.ys)])
#     db.add_signal(dbiso, data)
#     if m.fit:
#         # add fit
#         db.add_fit(dbhist, dbiso, fit=m.fit)
#
#     if kind in ('signal', 'baseline'):
#         # add isotope result
#         db.add_isotope_result(dbiso,
#                               dbhist,
#                               signal_=float(m.value), signal_err=float(m.error))

# def _save_isotope_info(self, analysis, signals):
#     self.info('saving isotope info')
#     # def func_peak_hop():
#     #     db = self.db
#     #
#     #     # add fit history
#     #     dbhist = db.add_fit_history(analysis,
#     #                                 user=self.spec.username)
#     #     for iso in self.arar_age.isotopes.itervalues():
#     #         detname=iso.detector
#     #         det = db.get_detector(detname)
#     #         if det is None:
#     #             det = db.add_detector(detname)
#     #             db.sess.flush()
#
#
#
#     def func():
#         db = self.db
#
#         # add fit history
#         dbhist = db.add_fit_history(analysis,
#                                     user=self.spec.username)
#
#         key = lambda x: x[1]
#         si = sorted(self._save_isotopes, key=key)
#
#         for detname, isos in groupby(si, key=key):
#             det = db.get_detector(detname)
#             if det is None:
#                 det = db.add_detector(detname)
#                 db.sess.flush()
#
#             for iso, detname, kind in isos:
#                 # add isotope
#                 dbiso = db.add_isotope(analysis, iso, det,
#                                        kind=kind)
#                 db.sess.flush()
#
#                 s = signals['{}{}'.format(iso, kind)]
#
#                 # add signal data
#                 data = ''.join([struct.pack('>ff', x, y)
#                                 for x, y in zip(s.xs, s.ys)])
#                 db.add_signal(dbiso, data)
#
#                 if s.fit:
#                     # add fit
#                     db.add_fit(dbhist, dbiso, fit=s.fit)
#
#                 if kind in ['signal', 'baseline']:
#                     # add isotope result
#                     db.add_isotope_result(dbiso,
#                                           dbhist,
#                                           signal_=float(s.value), signal_err=float(s.error))
#
#     if self.is_peak_hop:
#         func()
#     else:
#         func()
# return self._time_save(func, 'isotope info')

# def _preliminary_processing(self, p):
#     self.info('organizing data for database save')
#     dm = self.data_manager
#     dm.open_data(p)
#     signals = [(iso, detname)
#                for (iso, detname, kind) in self._save_isotopes
#                if kind == 'signal']
#     baselines = [(iso, detname)
#                  for (iso, detname, kind) in self._save_isotopes
#                  if kind == 'baseline']
#     sniffs = [(iso, detname)
#               for (iso, detname, kind) in self._save_isotopes
#               if kind == 'sniff']
#
#     rsignals = dict()
#
#     def extract_xy(tb):
#         try:
#             x, y = zip(*[(r['time'], r['value']) for r in tb.iterrows()])
#         except ValueError:
#             x, y = [], []
#         return x, y
#
#     #fits = self.plot_panel.fits
#     #for fit, (iso, detname) in zip(fits, signals):
#     for iso, detname in signals:
#         try:
#             fit = self.arar_age.isotopes[iso].fit
#         except (AttributeError, KeyError):
#             fit = 'linear'
#
#         tab = dm.get_table(detname, '/signal/{}'.format(iso))
#         x, y = extract_xy(tab)
#
#         #            if iso=='Ar40':
#         #                print 'prelim signal,',len(x), x[0], x[-1]
#         s = IsotopicMeasurement(xs=x, ys=y, fit=fit)
#         #            print 'signal',iso, s.value, y
#         rsignals['{}signal'.format(iso)] = s
#
#
#     #baseline_fits = ['average_SEM', ] * len(baselines)
#     #for fit, (iso, detname) in zip(baseline_fits, baselines):
#     for iso, detname in baselines:
#         try:
#             fit = self.arar_age.isotopes[iso].baseline.fit
#         except (AttributeError, KeyError):
#             fit = 'average_SEM'
#
#         tab = dm.get_table(detname, '/baseline/{}'.format(iso))
#         x, y = extract_xy(tab)
#
#         bs = IsotopicMeasurement(xs=x, ys=y, fit=fit)
#         #            print 'baseline',iso, bs.value, y
#
#         rsignals['{}baseline'.format(iso)] = bs
#
#     for (iso, detname) in sniffs:
#         tab = dm.get_table(detname, '/sniff/{}'.format(iso))
#
#         x, y = extract_xy(tab)
#         sn = IsotopicMeasurement(xs=x, ys=y)
#
#         rsignals['{}sniff'.format(iso)] = sn
#
#     #         peak_center = dm.get_table('peak_center', '/')
#     dm.close_file()
#     return rsignals

#     def _get_fit_block(self, iter_cnt, fits):
#         for sli, fs in fits:
#             if sli:
#
#                 s, e = sli
#                 if s is None:
#                     s = 0
#                 if e is None:
#                     e = Inf
#
#                 if iter_cnt > s and iter_cnt < e:
#                     break
#         return fs

#     def _make_write_iteration(self, grpname, data_write_hook,
#                          series, fits, refresh, graph):
#         def _write(data):
#             dets = self._active_detectors
#             i, x, intensities = data
#             nfs = self._get_fit_block(i, fits)
#             keys, signals = intensities
#             if graph:
#                 if grpname == 'signal':
#                     self.plot_panel.fits = nfs
#
#     #             self.signals = weakref.ref(dict(zip(keys, signals)))()
#                 for pi, (fi, dn) in enumerate(zip(nfs, dets)):
#                     signal = signals[keys.index(dn.name)]
#                     graph.add_datum((x, signal),
#                                     series=series,
#                                     plotid=pi,
#                                     update_y_limits=True,
#                                     ypadding='0.1'
#                                     )
#                     if fi:
#                         graph.set_fit(fi, plotid=pi, series=0)
#
#             data_write_hook(dets, x, keys, signals)
#
#             if refresh and graph:
# #                 pass
#                 # only refresh regression every 5th iteration
# #                 test if graph.refresh is consuming memory
# #                 if i % 5 == 0 or i < 10:
#                 graph.refresh()
#
#         return _write
#     def _measure2(self, grpname, data_write_hook,
#                            ncounts, starttime, starttime_offset,
#                             series, fits, check_conditions, refresh):
# #         print '------------------------{}----------------------------'.format(grpname)
# #         before = measure_type()
#
#         mem_log('pre measure {}'.format(grpname))
# #         st = time.time()
#
#         if not self.spectrometer_manager:
#             self.warning('no spectrometer manager')
#             return True
#
#         self.info('measuring {}. ncounts={}'.format(grpname, ncounts),
#                   color=MEASUREMENT_COLOR)
#
#         self._total_counts += ncounts
#
# #         spectrometer = self.spectrometer_manager.spectrometer
# #         get_data = lambda: self.spectrometer_manager.spectrometer.get_intensities(tagged=True)
# #         get_data = self._get_data_generator()
#
#         ncounts = int(ncounts)
# #         iter_cnt = 1
#         graph = None
#         if self.plot_panel:
#             graph = self.plot_panel.isotope_graph
#             mi, ma = graph.get_x_limits()
#             dev = (ma - mi) * 0.05
#             if (self._total_counts + dev) > ma:
#                 graph.set_x_limits(-starttime_offset, self._total_counts + (ma - mi) * 0.25)
#             elif starttime_offset > mi:
#                 graph.set_x_limits(min_=-starttime_offset)
#             nfs = self._get_fit_block(0, fits)
#     #         for pi, (fi, dn) in enumerate(zip(nfs, dets)):
#             for pi, fi in enumerate(nfs):
#                 graph.new_series(marker='circle', type='scatter',
#                                  marker_size=1.25,
#                                  fit=fi,
#                                  plotid=pi
#                                  )
#
#         func = self._make_write_iteration(grpname, data_write_hook,
#                                                     series, fits, refresh,
#                                                     graph)
#         dm = self.data_manager
#         with dm.open_file(self._current_data_frame):
#             with consumable(func) as con:
#                 self._iteration(con, ncounts, check_conditions, starttime)
#
#         if graph:
#             graph.refresh()
#
#         mem_log('post measure {}'.format(grpname))
#
#         return True
#
#     def _iteration(self, con, ncounts, check_conditions, starttime):
#         st = time.time()
#         if starttime is None:
#             starttime = time.time()
#
#         iter_cnt = 1
#         iter_step = self._iter_step
#         get_data = self._get_data_generator()
#
#         debug = globalv.experiment_debug
#         if debug:
#             m = 0.2
#         else:
#             m = self.integration_time
#
#         check = lambda x: self._check_iteration(x, ncounts, check_conditions)
#         while 1:
# #             if iter_cnt > ncounts:
# #                 break
#             ck = check(iter_cnt)
#             if ck == 'break':
#                 break
#             elif ck == 'cancel':
#                 return False
#
#             data = get_data.next()
#             iter_step(iter_cnt, con, data, starttime, m, debug)
#             iter_cnt += 1
#
#         t = time.time() - st
#         iter_cnt -= 1
#         et = iter_cnt * self.integration_time
#         self.debug('%%%%%%%%%%%%%%%%%%%%%%%% counts: {} {} {}'.format(iter_cnt, et, t))

#     @profile
#     def _iter_step(self, iter_cnt, con, data, starttime, period, debug=False):
#
#         x = time.time() - starttime  # if not self._debug else iter_cnt + starttime
#         if debug:
#             x *= period ** -1
#         con.add_consumable((iter_cnt, x, data))
#
#         if iter_cnt % 50 == 0:
#             self.info('collecting point {}'.format(iter_cnt))
# #             mem_log('collecting point {}'.format(iter_cnt))
#
#         iter_cnt += 1
#         time.sleep(period)

#     def _check_conditions(self, conditions, cnt):
#         for ti in conditions:
#             if ti.check(self.arar_age, cnt):
#                 return ti
#
#     def _check_iteration(self, i, ncounts, check_conditions):
#
# #         if self.plot_panel is None:
# #             return 'break'
#
#         j = i - 1
#         # exit the while loop if counts greater than max of original counts and the plot_panel counts
#         pc = 0
#         if self.plot_panel:
#             pc = self.plot_panel.ncounts
#
#         maxcounts = max(ncounts, pc)
#         if i > maxcounts:
#             return 'break'
#
#         if check_conditions:
#             termination_condition = self._check_conditions(self.termination_conditions, i)
#             if termination_condition:
#                 self.info('termination condition {}. measurement iteration executed {}/{} counts'.format(termination_condition.message, j, ncounts),
#                           color='red'
#                           )
#                 return 'cancel'
#
#             truncation_condition = self._check_conditions(self.truncation_conditions, i)
#             if truncation_condition:
#                 self.info('truncation condition {}. measurement iteration executed {}/{} counts'.format(truncation_condition.message, j, ncounts),
#                           color='red'
#                           )
#                 self.state = 'truncated'
#                 self.measurement_script.abbreviated_count_ratio = truncation_condition.abbreviated_count_ratio
#
# #                self.condition_truncated = True
#                 return 'break'
#
#             action_condition = self._check_conditions(self.action_conditions, i)
#             if action_condition:
#                 self.info('action condition {}. measurement iteration executed {}/{} counts'.format(action_condition.message, j, ncounts),
#                           color='red'
#                           )
#                 action_condition.perform(self.measurement_script)
#                 if not action_condition.resume:
#                     return 'break'
#
#         if i > self.measurement_script.ncounts:
#             self.info('script termination. measurement iteration executed {}/{} counts'.format(j, ncounts))
#             return 'break'
#
#         if pc:
#             if i > pc:
#                 self.info('user termination. measurement iteration executed {}/{} counts'.format(j, ncounts))
#                 self._total_counts -= (ncounts - i)
#                 return 'break'
#
#         if self._truncate_signal:
#             self.info('measurement iteration executed {}/{} counts'.format(j, ncounts))
#             self._truncate_signal = False
#
#             return 'break'
#
#         if not self._alive:
#             self.info('measurement iteration executed {}/{} counts'.format(j, ncounts))
#             return 'cancel'
