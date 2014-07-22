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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Event, Button, String, \
    Bool, Enum, Property, Instance, Int, List, Any, Color, Dict, on_trait_change
# from traitsui.api import View, Item
# from apptools.preferences.preference_binding import bind_preference
from pyface.constant import CANCEL, YES, NO
from pyface.timer.do_later import do_after

#============= standard library imports ========================
from threading import Thread, Event as Flag, Lock
import weakref
import time
from sqlalchemy.orm.exc import NoResultFound
import os
#============= local library imports  ==========================
# from pychron.core.ui.thread import Thread as uThread
# from pychron.loggable import Loggable
from pychron.displays.display import DisplayController
from pychron.experiment.connectable import Connectable
from pychron.experiment.datahub import Datahub
from pychron.experiment.user_notifier import UserNotifier
from pychron.experiment.utilities.identifier import convert_extract_device
from pychron.external_pipette.protocol import IPipetteManager
from pychron.initialization_parser import InitializationParser
from pychron.loggable import Loggable
from pychron.pyscripts.pyscript_runner import RemotePyScriptRunner, PyScriptRunner
from pychron.monitors.automated_run_monitor import AutomatedRunMonitor, \
    RemoteAutomatedRunMonitor
from pychron.experiment.stats import StatsGroup
from pychron.pychron_constants import NULL_STR
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager

from pychron.database.orms.isotope.meas import meas_AnalysisTable, meas_MeasurementTable, meas_ExtractionTable
from pychron.database.orms.isotope.gen import gen_ExtractionDeviceTable, gen_MassSpectrometerTable, \
    gen_AnalysisTypeTable

from pychron.core.codetools.memory_usage import mem_available, mem_log
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.consumer_mixin import consumable
from pychron.paths import paths
from pychron.experiment.automated_run.automated_run import AutomatedRun
from pychron.core.helpers.filetools import add_extension
from pychron.globals import globalv
from pychron.core.ui.preference_binding import bind_preference, color_bind_preference
from pychron.wait.wait_group import WaitGroup


class ExperimentExecutor(Loggable):
    experiment_queues = List
    experiment_queue = Any
    user_notifier = Instance(UserNotifier, ())
    connectables = List
    #===========================================================================
    # control
    #===========================================================================
    start_button = Event
    stop_button = Event
    can_start = Property(depends_on='executable, _alive')
    #     execute_button = Event
    #     resume_button = Button('Resume')
    #     delay_between_runs_readback = Float
    delaying_between_runs = Bool

    extraction_state_label = String
    extraction_state_color = Color

    end_at_run_completion = Bool(False)
    cancel_run_button = Button('Cancel Run')
    #     execute_label = Property(depends_on='_alive')

    truncate_button = Button('Truncate Run')
    truncate_style = Enum('Normal', 'Quick')
    '''
        immediate 0= measure_iteration stopped at current step, script continues
        quick     1= measure_iteration stopped at current step, script continues using 0.25*counts
        
        old-style
            immediate 0= is the standard truncation, measure_iteration stopped at current step and measurement_script truncated
            quick     1= the current measure_iteration is truncated and a quick baseline is collected, peak center?
            next_int. 2= same as setting ncounts to < current step. measure_iteration is truncated but script continues
    '''
    #===========================================================================
    #
    #===========================================================================
    console_display = Instance(DisplayController)
    console_updated = Event
    wait_group = Instance(WaitGroup, ())
    stats = Instance(StatsGroup)

    spectrometer_manager = Any
    extraction_line_manager = Any
    ion_optics_manager = Any

    pyscript_runner = Instance(PyScriptRunner)
    monitor = Instance(AutomatedRunMonitor)
    # current_run = Instance(AutomatedRun)

    measuring_run = Instance(AutomatedRun)
    extracting_run = Instance(AutomatedRun)

    datahub = Instance(Datahub)
    #===========================================================================
    #
    #===========================================================================
    queue_modified = False

    executable = Bool
    measuring = Bool(False)
    extracting = Bool(False)

    mode = 'normal'
    #===========================================================================
    # preferences
    #===========================================================================
    auto_save_delay = Int(30)
    use_auto_save = Bool(True)
    min_ms_pumptime = Int(30)

    use_memory_check = Bool(True)
    memory_threshold = Int

    _alive = Bool(False)
    _canceled = False
    _state_thread = None

    _end_flag = None
    _complete_flag = None

    _prev_blanks = Dict
    _prev_baselines = Dict
    _err_message = String

    baseline_color = Color
    sniff_color = Color
    signal_color = Color


    def __init__(self, *args, **kw):
        super(ExperimentExecutor, self).__init__(*args, **kw)
        self.wait_control_lock = Lock()

        self.monitor = self._monitor_factory()

    def set_queue_modified(self):
        self.queue_modified = True

    def get_prev_baselines(self):
        return self._prev_baselines

    def get_prev_blanks(self):
        return self._prev_blanks

    def warning(self, msg, log=True, color=None, *args, **kw):

        super(ExperimentExecutor, self).warning(msg, *args, **kw)

        if color is None:
            color = 'red'

        msg = msg.upper()
        if self.console_display:
            self.console_display.add_text(msg, color=color)

        self.console_updated = '{}|{}'.format(color, msg)

    def info_marker(self, char='=', color=None):
        if color is None:
            color = 'green'
        if self.console_display:
            self.console_display.add_marker(char, color=color)

    def info(self, msg, log=True, color=None, *args, **kw):
        if color is None:
            color = 'green'

        if self.console_display:
            self.console_display.add_text(msg, color=color)

        if log:
            super(ExperimentExecutor, self).info(msg, *args, **kw)

        self.console_updated = '{}|{}'.format(color, msg)

    def bind_preferences(self):
        # super(ExperimentExecutor, self).bind_preferences()

        self.datahub.bind_preferences()

        prefid = 'pychron.experiment'
        #auto save
        bind_preference(self, 'use_auto_save',
                        '{}.use_auto_save'.format(prefid))
        bind_preference(self, 'auto_save_delay',
                        '{}.auto_save_delay'.format(prefid))
        bind_preference(self, 'min_ms_pumptime', '{}.min_ms_pumptime'.format(prefid))

        #colors
        color_bind_preference(self, 'signal_color',
                              '{}.signal_color'.format(prefid))
        color_bind_preference(self, 'sniff_color',
                              '{}.sniff_color'.format(prefid))
        color_bind_preference(self, 'baseline_color',
                              '{}.baseline_color'.format(prefid))

        #user_notifier
        bind_preference(self.user_notifier.emailer, 'server_username', '{}.server_username'.format(prefid))
        bind_preference(self.user_notifier.emailer, 'server_password', '{}.server_password'.format(prefid))
        bind_preference(self.user_notifier.emailer, 'server_host', '{}.server_host'.format(prefid))
        bind_preference(self.user_notifier.emailer, 'server_port', '{}.server_port'.format(prefid))

        #memory
        bind_preference(self, 'use_memory_check', '{}.use_memory_check'.format(prefid))
        bind_preference(self, 'memory_threshold', '{}.memory_threshold'.format(prefid))

    def isAlive(self):
        return self._alive

    def reset(self):
        pass

    def cancel(self, *args, **kw):
        self._cancel(*args, **kw)

    def set_extract_state(self, state, flash=0.75, color='green', period=1.5):
        self._set_extract_state(state, flash, color, period=period)

    def info_heading(self, msg):
        self.info('')
        self.info_marker('=')
        self.info(msg)
        self.info_marker('=')
        self.info('')

    def execute(self):

        if self._pre_execute_check():
            self._alive = True
            self.end_at_run_completion = False

            name = self.experiment_queue.name

            msg = 'Starting Execution "{}"'.format(name)
            self.info_heading(msg)

            if self.stats:
                self.stats.reset()
                self.stats.start_timer()

            self._canceled = False
            self.extraction_state_label = ''

            self.experiment_queue.executed = True
            t = Thread(name='execute_exp',
                       target=self._execute)
            t.start()
            return t
        else:
            self._alive = False

    def wait(self, t, msg=''):
        self._wait(t, msg)

    def get_wait_control(self):
        with self.wait_control_lock:
            wd = self.wait_group.active_control
            if wd.is_active():
                wd = self.wait_group.add_control()
        return wd

    def stop(self):
        if self.delaying_between_runs:
            self._alive = False
            self.stats.stop_timer()
            self.wait_group.stop()
            #            self.wait_group.active_control.stop
            #            self.active_wait_control.stop()
            #             self.wait_dialog.stop()

            msg = '{} Stopped'.format(self.experiment_queue.name)
            self._set_message(msg, color='orange')
        else:
            self.cancel()

    def _set_message(self, msg, color='black'):

        self.info_heading(msg)
        invoke_in_main_thread(self.trait_set, extraction_state_label=msg,
                              extraction_state_color=color)

    def experiment_blob(self):
        path = self.experiment_queue.path
        path = add_extension(path, '.txt')
        if os.path.isfile(path):
            with open(path, 'r') as fp:
                return '{}\n{}'.format(path,
                                       fp.read())
        else:
            self.warning('{} is not a valid file'.format(path))

    #===============================================================================
    # private
    #===============================================================================
    def _execute(self):

        # delay before starting
        exp = self.experiment_queue
        delay = exp.delay_before_analyses
        self._delay(delay, message='before')

        for i, exp in enumerate(self.experiment_queues):
            if self.isAlive():
                self._execute_queue(i, exp)
            else:
                self.debug('No alive. not starting {},{}'.format(i, exp.name))

            if self.end_at_run_completion:
                self.debug('Previous queue ended at completion. Not continuing to other opened experiments')
                break

        self._alive = False

    def _execute_queue(self, i, exp):
        self.experiment_queue = exp
        self.info('Starting automated runs set={:02n} {}'.format(i, exp.name))

        # save experiment to database
        self.info('saving experiment "{}" to database'.format(exp.name))

        self.datahub.add_experiment(exp)

        exp.executed = True
        # scroll to the first run
        exp.automated_runs_scroll_to_row = 0

        last_runid = None

        rgen, nruns = exp.new_runs_generator()

        cnt = 0
        total_cnt = 0
        is_first_flag = True
        is_first_analysis = True
        with consumable(func=self._overlapped_run) as con:
            while 1:
                if not self.isAlive():
                    break

                if self._pre_run_check():
                    self.debug('pre run check failed')
                    break

                if self.queue_modified:
                    self.debug('Queue modified. making new run generator')
                    rgen, nruns = exp.new_runs_generator()
                    cnt = 0
                    self.queue_modified = False

                self.ms_pumptime_start = None
                # overlapping = self.current_run and self.current_run.isAlive()
                overlapping = self.measuring_run and self.measuring_run.isAlive()
                if not overlapping:
                    if self.isAlive() and cnt < nruns and not is_first_analysis:
                        # delay between runs
                        self._delay(exp.delay_between_analyses)
                    else:
                        self.debug('not delaying between runs isAlive={}, '
                                   'cnts<nruns={}, is_first_analysis={}'.format(self.isAlive(),
                                                                                cnt < nruns, is_first_analysis))

                try:
                    spec = rgen.next()
                except StopIteration:
                    self.debug('stop iteration')
                    break

                run = self._make_run(spec)
                if run is None:
                    break

                self.wait_group.active_control.page_name = run.runid
                run.is_first = is_first_flag

                if not run.is_last and run.spec.analysis_type == 'unknown' and spec.overlap[0]:
                    self.debug('waiting for extracting_run to finish')
                    self._wait_for(lambda x: self.extracting_run)

                    self.info('overlaping')

                    t = Thread(target=self._do_run, args=(run,))
                    t.start()

                    run.wait_for_overlap()
                    is_first_flag = False

                    self.debug('overlap finished. starting next run')

                    con.add_consumable((t, run))
                else:
                    is_first_flag = True
                    last_runid = run.runid
                    self._join_run(spec, run)

                cnt += 1
                total_cnt += 1
                is_first_analysis = False
                if self.end_at_run_completion:
                    break

            if self.end_at_run_completion:
                #if overlapping run is a special labnumber cancel it and finish experiment
                if not self.extracting_run.spec.is_special():
                    self._wait_for(lambda x: self.extracting_run)
                else:
                    self.extracting_run.cancel_run()

                #wait for the measurement run to finish
                self._wait_for(lambda x: self.measuring_run)

            else:
                #wait for overlapped runs to finish.
                self._wait_for(lambda x: self.extracting_run or self.measuring_run)

        if self._err_message:
            self.warning('automated runs did not complete successfully')
            self.warning('error: {}'.format(self._err_message))

        self._end_runs()
        if last_runid:
            self.info('Automated runs ended at {}, runs executed={}'.format(last_runid, total_cnt))

        self.info_heading('experiment queue {} finished'.format(exp.name))
        self.user_notifier.notify(exp, last_runid, self._err_message)

    def _wait_for(self, pred, period=1):
        st = time.time()
        while 1:
            et = time.time() - st
            if not self._alive:
                break
            if not pred(et):
                break
            time.sleep(period)

    def _join_run(self, spec, run):
        #    def _join_run(self, spec, t, run):
        #        t.join()
        self.debug('join run')
        self._do_run(run)

        self.debug('{} finished'.format(run.runid))
        if self.isAlive():
            self.debug('spec analysis type {}'.format(spec.analysis_type))
            if spec.analysis_type.startswith('blank'):
                pb = run.get_baseline_corrected_signals()
                if pb is not None:
                    self._prev_blanks = pb
                    self.debug('previous blanks ={}'.format(pb))

        self._report_execution_state(run)
        run.teardown()
        mem_log('> end join')

    def _do_run(self, run):
        self.debug('do run')

        if self.stats:
            self.stats.setup_run_clock(run)

        mem_log('< start')

        run.state = 'not run'

        q = self.experiment_queue
        #is this the last run in the queue. queue is not empty until _start runs so n==1 means last run
        run.is_last = len(q.cleaned_automated_runs) == 1

        self.extracting_run = run
        st = time.time()
        for step in ('_start',
                     '_extraction',
                     '_measurement',
                     '_post_measurement'):

            if not self.isAlive():
                break

            if self.monitor.has_fatal_error():
                run.cancel()
                run.state = 'failed'
                break

            f = getattr(self, step)
            if not f(run):
                break
        else:
            self.debug('$$$$$$$$$$$$$$$$$$$$ state at run end {}'.format(run.state))
            if not run.state in ('truncated', 'canceled', 'failed'):
                run.state = 'success'

        if self.stats:
            # self.stats.nruns_finished += 1
            self.stats.finish_run()

        if run.state in ('success', 'truncated'):
            self.run_completed = run

        self._remove_backup(run.uuid)
        # check to see if action should be taken
        self._check_run_at_end(run)

        t = time.time() - st
        self.info('Automated run {} {} duration: {:0.3f} s'.format(run.runid, run.state, t))

        run.finish()

        self.wait_group.pop()

        mem_log('end run')

    def _overlapped_run(self, v):
        self._overlapping = True
        t, run = v
        #         while t.is_alive():
        #             time.sleep(1)
        self.debug('OVERLAPPING. waiting for run to finish')
        t.join()

        self.debug('{} finished'.format(run.runid))
        if run.analysis_type.startswith('blank'):
            pb = run.get_baseline_corrected_signals()
            if pb is not None:
                self._prev_blanks = pb
        self._report_execution_state(run)
        run.teardown()

    def _cancel(self, style='queue', cancel_run=False, msg=None, confirm=True):
        # arun = self.current_run
        arun = self.measuring_run

        #        arun = self.experiment_queue.current_run
        if style == 'queue':
            name = os.path.basename(self.experiment_queue.path)
            name, _ = os.path.splitext(name)
        else:
            name = arun.runid

        if name:
            ret = YES
            if confirm:
                m = '"{}" is in progress. Are you sure you want to cancel'.format(name)
                if msg:
                    m = '{}\n{}'.format(m, msg)

                ret = self.confirmation_dialog(m,
                                               title='Confirm Cancel',
                                               return_retval=True,
                                               timeout=30)

            if ret == YES:
                # stop queue
                if style == 'queue':
                    self._alive = False
                    self.stats.stop_timer()
                self.set_extract_state(False)
                self.wait_group.stop()
                self._canceled = True
                if arun:
                    if style == 'queue':
                        state = None
                        if cancel_run:
                            state = 'canceled'
                    else:
                        state = 'canceled'
                        arun.aliquot = 0

                    arun.cancel_run(state=state)
                    if self.extracting_run:
                        self.extracting_run.cancel_run(state=state)

                    # self.non_clear_update_needed = True
                    self.measuring_run = None

                    # self.current_run = None

    def _end_runs(self):
        #         self._last_ran = None
        if self.stats:
            self.stats.stop_timer()

        #         self.db.close()
        self.set_extract_state(False)
        #        self.extraction_state = False
        #        def _set_extraction_state():
        if self.end_at_run_completion:
            c = 'orange'
            msg = 'Stopped'
        else:
            if self._canceled:
                c = 'red'
                msg = 'Canceled'
            else:
                c = 'green'
                msg = 'Finished'

        n = self.experiment_queue.name
        msg = '{} {}'.format(n, msg)
        self._set_message(msg, c)

    #===============================================================================
    # execution steps
    #===============================================================================
    def _start(self, run):
        ret = True

        if not run.start():
            self._alive = False
            ret = False
            run.state = 'failed'

            msg = 'Run {} did not start properly'.format(run.runid)
            self._err_message = msg
            self._canceled = True
            self.information_dialog(msg)
        else:
            self.experiment_queue.set_run_inprogress(run.runid)

        return ret

    def _extraction(self, ai):
        self.extracting_run = ai
        ret = True
        if ai.start_extraction():
            self.extracting = True
            if not ai.do_extraction():
                ret = self._failed_execution_step('Extraction Failed')
        else:
            ret = ai.isAlive()

        self.trait_set(extraction_state_label='', extracting=False)
        self.extracting_run = None
        return ret

    def _measurement(self, ai):
        ret = True
        self.measuring_run = ai
        if ai.start_measurement():
            # only set to measuring (e.g switch to iso evo pane) if
            # automated run has a measurement_script
            self.measuring = True

            if not ai.do_measurement():
                ret = self._failed_execution_step('Measurement Failed')
        else:
            ret = ai.isAlive()

        self.measuring_run = None
        self.measuring = False
        return ret

    def _post_measurement(self, ai):
        if not ai.do_post_measurement():
            self._failed_execution_step('Post Measurement Failed')
        else:
            return True

    def _failed_execution_step(self, msg):
        if not self._canceled:
            self._err_message = msg
            self._alive = False
        return False

    #===============================================================================
    # utilities
    #===============================================================================
    def _report_execution_state(self, run):
        pass

    def _make_run(self, spec):

        exp = self.experiment_queue

        if not self._set_run_aliquot(spec):
            return

        #reuse run if not overlap
        # run = self.current_run if not spec.overlap[0] else None
        run = None
        arun = spec.make_run(run=run)
        arun.logger_name = 'AutomatedRun {}'.format(arun.runid)
        '''
            save this runs uuid to a hidden file
            used for analysis recovery
        '''
        if spec.end_after:
            self.end_at_run_completion = True
            arun.is_last = True

        self._add_backup(arun.uuid)

        arun.integration_time = 1.04
        arun.min_ms_pumptime = self.min_ms_pumptime

        arun.experiment_executor = weakref.ref(self)()

        arun.spectrometer_manager = self.spectrometer_manager
        arun.extraction_line_manager = self.extraction_line_manager
        arun.ion_optics_manager = self.ion_optics_manager

        # arun.persister.db = self.db
        # arun.persister.massspec_importer = self.massspec_importer
        arun.persister.datahub = self.datahub
        arun.persister.experiment_identifier = exp.database_identifier
        arun.persister.load_name = exp.load_name

        arun.use_syn_extraction = True

        arun.runner = self.pyscript_runner
        arun.extract_device = exp.extract_device

        mon = self.monitor
        if mon is not None:
            mon.automated_run = weakref.ref(arun)()
            arun.monitor = mon
            arun.persister.monitor = mon

        return arun

    def _set_run_aliquot(self, spec):
        if spec.conflicts_checked:
            return True

        #if a run in executed runs is in extraction or measurement state
        # we are in overlap mode
        dh = self.datahub

        ens = self.experiment_queue.executed_runs
        step_offset, aliquot_offset = 0, 0

        exs = [ai for ai in ens if ai.state in ('measurement', 'extraction')]
        if exs:
            if spec.is_step_heat():
                eruns = [(ei.labnumber, ei.aliquot) for ei in exs]
                step_offset = 1 if (spec.labnumber, spec.aliquot) in eruns else 0
            else:
                eruns = [ei.labnumber for ei in exs]
                aliquot_offset = 1 if spec.labnumber in eruns else 0

            conflict = dh.is_conflict(spec)
            if conflict:
                ret = self._in_conflict(spec, aliquot_offset, step_offset)
            else:
                dh.update_spec(spec, aliquot_offset, step_offset)
                ret = True
        else:
            conflict = dh.is_conflict(spec)
            if conflict:
                ret = self._in_conflict(spec, conflict)
            else:
                dh.update_spec(spec)
                ret = True

        return ret

    def _in_conflict(self, spec, conflict, aoffset=0, soffset=0):
        dh = self.datahub
        self._canceled = True
        self._err_message = 'Databases are in conflict. {}'.format(conflict)

        ret = self.confirmation_dialog('Databases are in conflict. '
                                       'Do you want to modify the Run Identifier to {}'.format(dh.new_runid),
                                       timeout_ret=0,
                                       timeout=30)
        if ret or ret == 0:
            dh.update_spec(spec, aoffset, soffset)
            ret = True
            self._canceled = False
            self._err_message = ''
        else:
            spec.conflicts_checked = False
            self.message(self._err_message)
            # self.info('No response from user. Canceling run')
            # do_later(self.information_dialog,
            #          'Databases are in conflict. No response from user. Canceling experiment')
        return ret

    def _delay(self, delay, message='between'):
        #        self.delaying_between_runs = True
        msg = 'Delay {} runs {} sec'.format(message, delay)
        self.info(msg)
        self._wait(delay, msg)
        self.delaying_between_runs = False

    def continued(self):
        self.stats.continue_run()

    def _wait(self, delay, msg):
        wg = self.wait_group
        wc = self.get_wait_control()

        wc.message = msg
        wc.start(wtime=delay)
        wg.pop(wc)

        if wc.is_continued():
            self.stats.continue_clock()

    def _set_extract_state(self, state, *args):
        """
            state: str
        """
        if state:
            self._extraction_state_on(state, *args)

        else:
            self._extraction_state_off()

    def _extraction_state_on(self, state, flash, color, period, end):
        """
            flash: float (0.0 - 1.0) percent of period to be on. e.g if flash=0.75 and period=4,
                    state displayed for 3 secs, then off for 1 sec
            color: str
            period: float
        """
        label = state.upper()
        if flash:
            if self._end_flag:
                self._end_flag.set()

                # wait until previous loop finished.
                cf = self._complete_flag
                while not cf.is_set():
                    time.sleep(0.05)

            else:
                self._end_flag = Flag()
                self._complete_flag = Flag()

            def pattern_gen():
                """
                    infinite generator
                """
                pattern = ((flash * period, True), ((1 - flash) * period, False))
                i = 0
                while 1:
                    try:
                        yield pattern[i]
                        i += 1
                    except IndexError:
                        yield pattern[0]
                        i = 1

            self._end_flag.clear()
            self._complete_flag.clear()

            invoke_in_main_thread(self._extraction_state_iter, pattern_gen(), label, color)
        else:
            invoke_in_main_thread(self.trait_set, extraction_state_label=label,
                                  extraction_state_color=color)

    def _extraction_state_off(self):
        if self._end_flag:
            self._end_flag.set()

        invoke_in_main_thread(self.trait_set, extraction_state_label='')

    def _extraction_state_iter(self, gen, label, color):
        t, state = gen.next()
        if state:
            self.trait_set(extraction_state_label=label,
                           extraction_state_color=color)
        else:
            self.trait_set(extraction_state_label='')

        if not self._end_flag.is_set():
            do_after(t * 1000, self._extraction_state_iter, gen, label, color)
        else:
            self._complete_flag.set()
            self.trait_set(extraction_state_label='')

    def _add_backup(self, uuid_str):
        with open(paths.backup_recovery_file, 'a') as fp:
            fp.write('{}\n'.format(uuid_str))

    def _remove_backup(self, uuid_str):
        with open(paths.backup_recovery_file, 'r') as fp:
            r = fp.read()

        r = r.replace('{}\n'.format(uuid_str), '')
        with open(paths.backup_recovery_file, 'w') as fp:
            fp.write(r)

    #===============================================================================
    # checks
    #===============================================================================
    def _check_run_at_end(self, run):
        """
            check to see if an action should be taken

            if runs  are overlapping this will be a problem.

            dont overlay onto blanks

            execute the action and continue the queue
        """
        exp = self.experiment_queue
        for action in exp.queue_actions:
            if action.check_run(run):
                self._do_action(action)
                break

    def _do_action(self, action):
        self.info('Do queue action {}'.format(action.action))
        if action.action == 'repeat':
            if action.count < action.nrepeat:
                self.debug('repeating last run')
                action.count += 1
                exp = self.experiment_queue

                run = exp.executed_runs[0]
                exp.automated_runs.insert(0, run)

                # experimentor handles the queue modified
                # resets the database and updates info
                self.queue_modified = True

            else:
                self.info('executed N {} {}s'.format(action.count + 1,
                                                     action.action))
                self.cancel(confirm=False)

        elif action.action == 'cancel':
            self.cancel(confirm=False)

    def _pre_run_check(self):
        """
            return True to stop execution loop
        """
        self.debug('pre run check')
        if self._check_memory():
            self._err_message = 'Not enough memory'
            return True

        if not self._check_managers():
            self._err_message = 'Not all managers available'
            return True

        if self.monitor:
            if not self.monitor.check():
                self._err_message = 'Automated Run Monitor failed'
                self.warning('automated run monitor failed')
                return True

        # if the experiment queue has been modified wait until saved or
        # timed out. if timed out autosave.
        self._wait_for_save()
        self.debug('pre run finished')

    def _check_memory(self, threshold=None):
        """
            if avaliable memory is less than threshold  (MB)
            stop the experiment
            issue a warning

            return True if out of memory
            otherwise None
        """
        if self.use_memory_check:
            if threshold is None:
                threshold = self.memory_threshold

            # return amem in MB
            amem = mem_available()
            self.debug('Available memory {}. mem-threshold= {}'.format(amem, threshold))
            if amem < threshold:
                msg = 'Memory limit exceeded. Only {} MB available. Stopping Experiment'.format(amem)
                invoke_in_main_thread(self.warning_dialog, msg)
                return True

    def _wait_for_save(self):
        """
            wait for experiment queue to be saved.

            actually wait until time out or self.executable==True
            executable set higher up by the Experimentor

            if timed out auto save or cancel

        """
        st = time.time()
        delay = self.auto_save_delay
        auto_save = self.use_auto_save

        if not self.executable:
            self.info('Waiting for save')
            cnt = 0

            while not self.executable:
                time.sleep(1)
                if time.time() - st < delay:
                    self.set_extract_state('Waiting for save. Autosave in {} s'.format(delay - cnt),
                                           flash=False)
                    cnt += 1
                else:
                    break

            if not self.executable:
                self.info('Timed out waiting for user input')
                if auto_save:
                    self.info('autosaving experiment queues')
                    self.set_extract_state('')
                    self.auto_save_event = True
                else:
                    self.info('canceling experiment queues')
                    self.cancel(confirm=False)

    def _pre_execute_check(self, inform=True):
        if not self.datahub.secondary_connect():
            if not self.confirmation_dialog(
                    'Not connected to a Mass Spec database. Do you want to continue with pychron only?'):
                return

        exp = self.experiment_queue
        runs = exp.cleaned_automated_runs
        if not len(runs):
            return

        # check the first aliquot before delaying
        arv = runs[0]
        if not self._set_run_aliquot(arv):
            return

        if globalv.experiment_debug:
            self.debug('********************** NOT DOING PRE EXECUTE CHECK ')
            return True

        if self._check_memory():
            return

        if not self._check_managers(inform=inform):
            return

        if self.monitor:
            self.monitor.set_additional_connections(self.connectables)
            self.monitor.clear_errors()
            if not self.monitor.check():
                self.warning_dialog('Automated Run Monitor Failed')
                return

        with self.datahub.mainstore.db.session_ctx():
            dbr = self._get_preceding_blank_or_background(inform=inform)
            if not dbr is True:
                if dbr is None:
                    return
                else:
                    self.info('using {} as the previous blank'.format(dbr.record_id))
                    self._prev_blanks = dbr.get_baseline_corrected_signal_dict()
                    self._prev_baselines = dbr.get_baseline_dict()

        if not self.pyscript_runner.connect():
            self.info('Failed connecting to pyscript_runner')
            msg = 'Failed connecting to a pyscript_runner. Is the extraction line computer running?'
            invoke_in_main_thread(self.warning_dialog, msg)
            return

        self.debug('pre check complete')
        return True

    def _get_preceding_blank_or_background(self, inform=True):
        #         msg = '''First "{}" not preceded by a blank.
        # If "Yes" use last "blank_{}"
        # Last Run= {}
        #
        # If "No" select from database
        # '''
        msg = '''First "{}" not preceded by a blank.
Use Last "blank_{}"= {}
'''
        exp = self.experiment_queue

        types = ['air', 'unknown', 'cocktail']
        # get first air, unknown or cocktail
        aruns = exp.cleaned_automated_runs

        an = next((a for a in aruns if a.analysis_type in types), None)

        if an:
            anidx = aruns.index(an)
            #find first blank_
            #if idx > than an idx need a blank
            nopreceding = True
            ban = next((a for a in aruns if a.analysis_type == 'blank_{}'.format(an.analysis_type)), None)
            if ban:
                nopreceding = aruns.index(ban) > anidx
            else:
                #if first run is a blank_... just use it
                if aruns[0].analysis_type.startswith('blank'):
                    return True

            if anidx == 0 or nopreceding:
                pdbr, selected = self._get_blank(an.analysis_type, exp.mass_spectrometer,
                                                 exp.extract_device,
                                                 last=True)
                if pdbr:
                    if selected:
                        return pdbr
                    else:
                        msg = msg.format(an.analysis_type,
                                         an.analysis_type,
                                         pdbr.record_id)

                        retval = NO
                        if inform:
                            retval = self.confirmation_dialog(msg,
                                                              no_label='Select From Database',
                                                              cancel=True,
                                                              return_retval=True)

                        if retval == CANCEL:
                            return
                        elif retval == YES:
                            return pdbr
                        else:
                            pdbr, _ = self._get_blank(an.analysis_type, exp.mass_spectrometer,
                                                      exp.extract_device)
                            return pdbr
                else:
                    self.warning_dialog('No blank for {} is in the database. Run a blank!!'.format(an.analysis_type))
                    return

        return True

    def _get_blank(self, kind, ms, ed, last=False):
        mainstore = self.datahub.mainstore
        db = mainstore.db
        selected = False
        with db.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(meas_MeasurementTable, gen_AnalysisTypeTable)

            if last:
                q = q.filter(gen_AnalysisTypeTable.name == 'blank_{}'.format(kind))
            else:
                q = q.filter(gen_AnalysisTypeTable.name.startswith('blank'))

            if ms:
                q = q.join(gen_MassSpectrometerTable)
                q = q.filter(gen_MassSpectrometerTable.name == ms.lower())
            if ed and not ed in ('Extract Device', NULL_STR) and kind == 'unknown':
                q = q.join(meas_ExtractionTable, gen_ExtractionDeviceTable)
                q = q.filter(gen_ExtractionDeviceTable.name == ed)

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            dbr = None
            if last:
                q = q.limit(1)
                try:
                    dbr = q.first()
                except NoResultFound, e:
                    self.debug('No result found {}'.format(e))
                except NoResultFound:
                    dbr = self._select_blank(db, ms)

                if dbr is None:
                    dbr = self._select_blank(db, ms)
                    selected = True
            else:
                dbr = self._select_blank(db, ms)

            if dbr:
                dbr = mainstore.make_analysis(dbr, calculate_age=False)

            return dbr, selected

    def _select_blank(self, db, ms):
        sel = db.selector_factory(style='single')
        sel.set_columns(exclude='irradiation_info',
                        append=[('Measurement', 'meas_script_name', 120),
                                ('Extraction', 'extract_script_name', 90)])
        sel.window_width = 750
        sel.title = 'Select Default Blank'

        with db.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(meas_MeasurementTable)
            q = q.join(gen_AnalysisTypeTable)

            q = q.filter(gen_AnalysisTypeTable.name.like('blank%'))
            if ms:
                q = q.join(gen_MassSpectrometerTable)
                q = q.filter(gen_MassSpectrometerTable.name == ms.lower())

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            q = q.limit(100)
            dbs = q.all()

            sel.load_records(dbs[::-1], load=False)
            sel.selected = sel.records[-1]
            info = sel.edit_traits(kind='livemodal')
            if info.result:
                return sel.selected

    def _check_managers(self, inform=True):
        self.debug('checking for managers')
        if globalv.experiment_debug:
            self.debug('********************** NOT DOING  managers check')
            return True

        # exp = self.experiment_queue
        # for i in range(n):
        #     nonfound = self._check_for_managers(exp)
        #     if not nonfound:
        #         break
        nonfound = self._check_for_managers()
        if nonfound:
            self.info('experiment canceled because could connect to managers {}'.format(nonfound))
            if inform:
                invoke_in_main_thread(self.warning_dialog,
                                      'Canceled! Could not connect to managers {}. '
                                      'Check that these instances are running.'.format(','.join(nonfound)))
            return

        return True

    def _check_for_managers(self):
        exp = self.experiment_queue
        nonfound = []
        elm_connectable = Connectable(name='Extraction Line')
        self.connectables = [elm_connectable]

        if self.extraction_line_manager is None:
            nonfound.append('extraction_line')
        else:
            if not self.extraction_line_manager.test_connection():
                nonfound.append('extraction_line')
            else:
                elm_connectable.connected = True

        if exp.extract_device and exp.extract_device not in (NULL_STR, 'Extract Device'):
            extract_device = convert_extract_device(exp.extract_device)
            ed_connectable = Connectable(name=exp.extract_device)
            self.connectables.append(ed_connectable)
            man = None
            if self.application:
                man = self.application.get_service(ILaserManager, 'name=="{}"'.format(extract_device))
                if man is None:
                    man = self.application.get_service(IPipetteManager, 'name=="{}"'.format(extract_device))

            if not man:
                nonfound.append(extract_device)
            else:
                if not man.test_connection():
                    nonfound.append(extract_device)
                else:
                    ed_connectable.set_connection_parameters(man)
                    ed_connectable.connected = True

        needs_spec_man = any([ai.measurement_script
                              for ai in exp.cleaned_automated_runs
                              if ai.state == 'not run'])

        if needs_spec_man:
            s_connectable = Connectable(name='Spectrometer')
            self.connectables.append(s_connectable)
            if self.spectrometer_manager is None:
                nonfound.append('spectrometer')
            else:
                if not self.spectrometer_manager.test_connection():
                    nonfound.append('spectrometer')
                else:
                    s_connectable.connected = True

        return nonfound

    #===============================================================================
    # handlers
    #===============================================================================
    def _current_run_changed(self):
        if self.current_run:
            self.current_run.is_last = self.end_at_run_completion

    def _end_at_run_completion_changed(self):
        if self.end_at_run_completion:
            if self.current_run:
                self.current_run.is_last = True
        else:
            self._update_automated_runs()

    @on_trait_change('experiment_queue:automated_runs[]')
    def _update_automated_runs(self):
        if self.isAlive():
            is_last = len(self.experiment_queue.cleaned_automated_runs) == 0

            self.extracting_run.is_last = is_last

    def _cancel_run_button_fired(self):
        self.debug('cancel run {}'.format(self.isAlive()))
        if self.isAlive():
            crun = self.measuring_run
            self.debug('cancel run {}'.format(crun))
            if crun:
                t = Thread(target=self.cancel, kwargs={'style': 'run'})
                t.start()
                #                 self._cancel_thread = t

    def _truncate_button_fired(self):
        if self.measuring_run:
            self.measuring_run.truncate_run(self.truncate_style)

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_can_start(self):
        return self.executable and not self.isAlive()

    #===============================================================================
    # defaults
    #===============================================================================
    def _datahub_default(self):
        dh = Datahub()
        return dh

    def _console_display_default(self):
        return DisplayController(
            bgcolor='black',
            default_color='limegreen',
            max_blocks=100)

    def _pyscript_runner_default(self):
        if self.mode == 'client':
            #            em = self.extraction_line_manager
            ip = InitializationParser()
            elm = ip.get_plugin('Experiment', category='general')
            runner = elm.find('runner')
            host, port, kind = None, None, None

            if runner is not None:
                comms = runner.find('communications')
                host = comms.find('host')
                port = comms.find('port')
                kind = comms.find('kind')

            if host is not None:
                host = host.text  # if host else 'localhost'
            if port is not None:
                port = int(port.text)  # if port else 1061
                kind = kind.text  # if kind else 'udp'

            runner = RemotePyScriptRunner(host, port, kind)
        else:
            runner = PyScriptRunner()

        return runner

    def _monitor_factory(self):
        # mon = None
        # isok = True
        self.debug('Experiment Executor mode={}'.format(self.mode))
        if self.mode == 'client':
            # self._check_for_managers()
            mon = RemoteAutomatedRunMonitor(name='automated_run_monitor')
            # ip = InitializationParser()
            # exp = ip.get_plugin('Experiment', category='general')
            # monitor = exp.find('monitor')
            # if monitor is not None:
            # if to_bool(monitor.get('enabled')):
            #         host, port, kind = None, None, None
            #         comms = monitor.find('communications')
            #         host = comms.find('host')
            #         port = comms.find('port')
            #         kind = comms.find('kind')
            #
            #         if host is not None:
            #             host = host.text  # if host else 'localhost'
            #         if port is not None:
            #             port = int(port.text)  # if port else 1061
            #         if kind is not None:
            #             kind = kind.text
            #         mon = RemoteAutomatedRunMonitor(host, port, kind, name=monitor.text.strip())
        else:
            mon = AutomatedRunMonitor()

        self.debug('Automated run monitor {}'.format(mon))
        if mon is not None:
            isok = mon.load()
            if isok:
                return mon
            else:
                self.warning('no automated run monitor avaliable. '
                             'Make sure config file is located at setupfiles/monitors/automated_run_monitor.cfg')

#============= EOF =============================================
