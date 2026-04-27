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

import os
import time
from contextvars import copy_context
from datetime import datetime
from operator import itemgetter
from queue import Queue, Empty
from threading import Thread, Lock, current_thread, main_thread, Event as TEvent
from typing import Any, Callable, Optional

from pyface.constant import CANCEL, YES, NO
from pyface.timer.do_later import do_after
from sqlalchemy.exc import DatabaseError
from traitsui.api import View, EnumEditor, Item, UItem
from traits.api import (
    Event,
    String,
    Bool,
    Enum,
    Property,
    Instance,
    Int,
    List,
    Any,
    Dict,
    on_trait_change,
    Float,
    Str,
)
from traits.trait_errors import TraitError
from pyface.ui_traits import PyfaceColor
from uncertainties import nominal_value, std_dev

from pychron.consumer_mixin import consumable
from pychron.core.codetools.memory_usage import mem_available
from pychron.core.helpers.filetools import add_extension, get_path, unique_path2
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.logger_setup import add_root_handler, remove_root_handler
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.progress import open_progress
from pychron.core.pychron_traits import PositiveInteger
from pychron.core.stats import calculate_weighted_mean, calculate_mswd
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.wait.wait_group import WaitGroup
from pychron.core.yaml import yload
from pychron.envisage.consoleable import Consoleable
from pychron.envisage.preference_mixin import PreferenceMixin
from pychron.envisage.view_util import open_view
from pychron.experiment import events, PreExecuteCheckException
from pychron.experiment.automated_run.persistence import ExcelPersister
from pychron.experiment.automated_run.syn_extraction import SynExtractionCollector
from pychron.experiment.state_machines import ExecutorController, TransitionRecord
from pychron.experiment.conditional.conditional import conditionals_from_file
from pychron.experiment.conditional.conditionals_view import ConditionalsView
from pychron.experiment.conflict_resolver import ConflictResolver
from pychron.experiment.datahub import Datahub
from pychron.experiment.experiment_scheduler import ExperimentScheduler
from pychron.experiment.experiment_status import ExperimentStatus
from pychron.experiment.telemetry.span import Span
from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.event import TelemetryEvent, EventType
from pychron.experiment.telemetry.device_io import get_last_device_io_snapshot
from pychron.experiment.telemetry.span import set_global_recorder
from pychron.observability import experiment_lifecycle
from pychron.experiment.state_machines.executor_machine import (
    ABORTED as EXEC_ABORTED,
    CANCELED as EXEC_CANCELED,
    COMPLETED as EXEC_COMPLETED,
    FAILED as EXEC_FAILED,
)
from pychron.experiment.state_machines.queue_machine import (
    QUEUE_ABORTED,
    QUEUE_CANCELED,
    QUEUE_COMPLETED,
    QUEUE_FAILED,
)
from pychron.experiment.state_machines.run_machine import (
    ABORT,
    CANCEL,
    CREATE,
    EXTRACTION_COMPLETE,
    EXTRACTION_FAILED,
    FINISH,
    MARK_INVALID,
    MEASUREMENT_COMPLETE,
    MEASUREMENT_FAILED,
    POST_MEASUREMENT_COMPLETE,
    POST_MEASUREMENT_FAILED,
    PRECHECK_FAILED as RUN_PRECHECK_FAILED,
    PRECHECK_PASSED as RUN_PRECHECK_PASSED,
    SAVE_COMPLETE as RUN_SAVE_COMPLETE,
    SAVE_FAILED,
    START,
    START_EXTRACTION,
    START_MEASUREMENT,
    START_POST_MEASUREMENT,
    START_SAVE,
    TRUNCATE,
)
from pychron.experiment.stats import StatsGroup
from pychron.experiment.utilities.conditionals import (
    test_queue_conditionals_name,
    SYSTEM,
    QUEUE,
    RUN,
    CONDITIONAL_GROUP_TAGS,
)
from pychron.experiment.utilities.conditionals_results import reset_conditional_results
from pychron.experiment.utilities.identifier import convert_extract_device, is_special
from pychron.experiment.utilities.repository_identifier import (
    retroactive_repository_identifiers,
    populate_repository_identifiers,
    get_curtag,
)
from pychron.extraction_line.ipyscript_runner import IPyScriptRunner
from pychron.globals import globalv
from pychron.options.options_manager import SeriesOptionsManager, OptionsController
from pychron.options.views.views import view
from pychron.paths import paths
from pychron.pipeline.plot.editors.series_editor import (
    SeriesEditor,
    AnalysisGroupedSeriesEditor,
)
from pychron.pipeline.plot.plotter.series import Series
from pychron.pychron_constants import (
    DEFAULT_INTEGRATION_TIME,
    AR_AR,
    DVC_PROTOCOL,
    DEFAULT_MONITOR_NAME,
    SCRIPT_NAMES,
    EM_SCRIPT_KEYS,
    NULL_STR,
    NULL_EXTRACT_DEVICES,
    IPIPETTE_PROTOCOL,
    ILASER_PROTOCOL,
    IFURNACE_PROTOCOL,
    CRYO_PROTOCOL,
    FAILED,
    CANCELED,
    TRUNCATED,
    SUCCESS,
    ARGON_KEYS,
)


def remove_backup(uuid_str):
    """
    remove uuid from backup recovery file
    """
    if not os.path.exists(paths.backup_recovery_file):
        return
    
    with open(paths.backup_recovery_file, "r") as rfile:
        r = rfile.read()

    r = r.replace("{}\n".format(uuid_str), "")
    with open(paths.backup_recovery_file, "w") as wfile:
        wfile.write(r)


class ExperimentExecutor(Consoleable, PreferenceMixin):
    """
    ExperimentExecutor coordinates execution of an experiment queue

    """

    experiment_queues = List
    experiment_queue = Any

    connectables = List
    active_editor = Any
    console_bgcolor = "black"
    selected_run = Instance(
        "pychron.experiment.automated_run.spec.AutomatedRunSpec",
    )
    autoplot_event = Event
    run_completed = Event

    ms_pumptime_start = None
    # ===========================================================================
    # control
    # ===========================================================================

    can_start = Property(depends_on="executable, alive")
    delaying_between_runs = Bool
    experiment_status = Instance(ExperimentStatus, ())

    end_at_run_completion = Bool(False)
    truncate_style = Enum("Normal", "Quick")
    """
        immediate 0= measure_iteration stopped at current step, script continues
        quick     1= measure_iteration stopped at current step, script continues using 0.25*counts

        old-style
            immediate 0= is the standard truncation, measure_iteration stopped at current step and measurement_script
                         truncated
            quick     1= the current measure_iteration is truncated and a quick baseline is collected, peak center?
            next_int. 2= same as setting ncounts to < current step. measure_iteration is truncated but script continues
    """
    # ===========================================================================
    #
    # ===========================================================================

    wait_group = Instance(WaitGroup, ())
    stats = Instance(StatsGroup, ())
    conditionals_view = Instance(ConditionalsView)
    spectrometer_manager = Any
    extraction_line_manager = Any
    ion_optics_manager = Any

    pyscript_runner = Instance(IPyScriptRunner)
    monitor = Instance("pychron.monitors.automated_run_monitor.AutomatedRunMonitor")

    measuring_run = Instance("pychron.experiment.automated_run.automated_run.AutomatedRun")
    extracting_run = Instance("pychron.experiment.automated_run.automated_run.AutomatedRun")

    datahub = Instance(Datahub)
    dashboard_client = Instance("pychron.dashboard.client.DashboardClient")

    scheduler = Instance(ExperimentScheduler)

    events = List

    timeseries_editor = Instance(AnalysisGroupedSeriesEditor)
    timeseries_refresh_button = Event
    timeseries_reset_button = Event
    # configure_timeseries_editor_button = Event
    # timeseries_options = Instance(SeriesOptionsManager)
    timeseries_n_recall = PositiveInteger(50)
    timeseries_mass_spectrometer = Str
    timeseries_mass_spectrometers = List
    # ===========================================================================
    #
    # ===========================================================================
    queue_modified = False

    executable = Bool
    measuring = Bool(False)
    extracting = Bool(False)

    mode = "normal"
    # ===========================================================================
    # preferences
    # ===========================================================================
    laboratory = Str
    auto_save_delay = Int(30)
    use_auto_save = Bool(True)

    use_dashboard_client = Bool
    min_ms_pumptime = Int(30)
    use_automated_run_monitor = Bool(False)
    set_integration_time_on_start = Bool(False)
    send_config_before_run = Bool(False)
    verify_spectrometer_configuration = Bool(False)
    default_integration_time = Float(DEFAULT_INTEGRATION_TIME)
    use_memory_check = Bool(True)
    memory_threshold = Int
    use_dvc = Bool(False)
    use_autoplot = Bool(False)
    monitor_name = DEFAULT_MONITOR_NAME
    experiment_type = Str(AR_AR)

    use_xls_persistence = Bool(False)
    use_db_persistence = Bool(True)

    ratio_change_detection_enabled = Bool(False)
    execute_open_queues = Bool(True)
    use_preceding_blank = Bool(True)
    save_all_runs = Bool(False)

    # dvc
    use_dvc_persistence = Bool(False)
    dvc_save_timeout_minutes = Int(5)
    use_dvc_overlap_save = Bool(False)
    default_principal_investigator = Str

    baseline_color = PyfaceColor
    sniff_color = PyfaceColor
    signal_color = PyfaceColor

    alive = Bool(False)
    _canceled = False
    _state_thread = None
    _aborted = False

    _end_flag = None
    _complete_flag = None

    _prev_blanks = Dict
    _prev_baselines = Dict
    _err_message = String

    _ratios = Dict
    _failure_counts = Dict
    _excluded_uuids = Dict

    _cv_info = None
    _cached_runs = List
    _active_repository_identifier = Str
    show_conditionals_event = Event
    diagnostic_stall_timeout = Float(120.0)
    diagnostic_progress_interval = Float(15.0)

    def __init__(self, *args, **kw):
        super(ExperimentExecutor, self).__init__(*args, **kw)
        self.wait_control_lock = Lock()
        self._exception_queue = Queue()
        self._save_complete_evt = TEvent()
        self._controller = ExecutorController(self)
        self._controller.register_on_transition(self._handle_state_transition)
        # Watchdog integration (Phase 6: executor integration)
        self._watchdog_integration = None
        self._last_progress_marker = ""
        self._last_progress_timestamp = 0.0
        self._last_stall_warning_timestamp = 0.0
        self._loop_heartbeat_timestamps = {}
        # Initialize UI state - ensure start button is enabled when no experiment is open
        self._sync_compatibility_state()
        # self.set_managers()
        # self.notification_manager = NotificationManager()

    def _handle_state_transition(self, machine_name: str, record: TransitionRecord) -> None:
        self._sync_compatibility_state()
        if machine_name == "executor" and not record.accepted:
            self.debug(
                "executor transition rejected event={} state={} reason={}".format(
                    record.event, record.old_state, record.reason
                )
            )

    def _set_ui_traits(self, wait: bool = False, **traits: Any) -> None:
        if not traits:
            return

        if current_thread() is main_thread():
            self.trait_set(**traits)
            return

        if wait:
            done = TEvent()

            def runner() -> None:
                try:
                    self.trait_set(**traits)
                finally:
                    done.set()

            invoke_in_main_thread(runner)
            done.wait()
        else:
            invoke_in_main_thread(self.trait_set, **traits)

    def _set_ui_event(self, name: str, value: Any = True) -> None:
        self._set_ui_traits(**{name: value})

    def _sync_compatibility_state(self) -> None:
        self._set_ui_traits(
            alive=self._controller.is_alive,
            measuring=self._controller.measuring,
            extracting=self._controller.extracting,
            end_at_run_completion=self._controller.end_at_run_completion,
        )

    def _set_executor_terminal_result(self, result: str, reason: str | None = None) -> None:
        self._controller.finalize_with_result(result, reason=reason)
        self._sync_compatibility_state()

    def _current_terminal_result(self) -> str:
        return self._controller.queue_terminal_result(self._err_message or None)

    def _should_stop_at_boundary(self) -> bool:
        return self._controller.should_end_at_run_completion()

    def _should_abort_execution(self) -> bool:
        return self._controller.should_abort()

    def _should_cancel_execution(self) -> bool:
        return self._controller.should_cancel() and not self._controller.should_abort()

    def _diagnostic_instrumentation_enabled(self) -> bool:
        return bool(
            self._controller.telemetry_recorder
            or getattr(globalv, "telemetry_enabled", False)
            or getattr(globalv, "experiment_debug", False)
        )

    def _current_run_ids(self) -> list[str]:
        run_ids = []
        for run in (self.extracting_run, self.measuring_run):
            if run is not None:
                run_ids.append(str(getattr(run, "runid", getattr(run, "uuid", "unknown-run"))))
        return run_ids

    def _controller_state_snapshot(self) -> dict[str, Any]:
        queue_state = None
        if self._controller.queue_machine is not None:
            queue_state = self._controller.queue_machine.observed_state

        active_run_states = {}
        for run_id, machine in self._controller.active_run_machines:
            active_run_states[run_id] = machine.observed_state

        return {
            "executor_state": self._controller.executor_machine.observed_state,
            "queue_state": queue_state,
            "active_run_states": active_run_states,
        }

    def _progress_payload(
        self,
        marker: str,
        run: Any = None,
        step: Optional[str] = None,
        elapsed_s: Optional[float] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        queue_name = getattr(self.experiment_queue, "name", None)
        run_state = None
        run_id = None
        if run is not None:
            run_id = getattr(run, "runid", None) or getattr(run, "uuid", None)
            run_state = getattr(getattr(run, "spec", None), "state", None)

        payload = {
            "marker": marker,
            "queue_name": queue_name,
            "run_id": run_id,
            "run_state": run_state,
            "step": step,
            "elapsed_s": elapsed_s,
            "alive": self.alive,
            "cancel_requested": self._should_cancel_execution(),
            "abort_requested": self._should_abort_execution(),
            "active_run_ids": self._current_run_ids(),
        }
        payload.update(self._controller_state_snapshot())
        if extra:
            payload.update(extra)
        return payload

    def _record_execution_event(
        self,
        marker: str,
        *,
        run: Any = None,
        step: Optional[str] = None,
        elapsed_s: Optional[float] = None,
        level: str = "debug",
        event_type: str = EventType.EXECUTION_PROGRESS.value,
        extra: Optional[dict[str, Any]] = None,
        flush: bool = False,
    ) -> None:
        payload = self._progress_payload(
            marker, run=run, step=step, elapsed_s=elapsed_s, extra=extra
        )
        self.debug(
            "executor progress marker={} queue={} run={} step={} elapsed_s={}".format(
                marker,
                payload.get("queue_name"),
                payload.get("run_id"),
                step,
                elapsed_s,
            )
        )
        recorder = self._controller.telemetry_recorder
        if recorder is not None:
            event = TelemetryEvent(
                event_type=event_type,
                ts=time.time(),
                level=level,
                queue_id=TelemetryContext.get_queue_id(),
                run_id=TelemetryContext.get_run_id(),
                run_uuid=TelemetryContext.get_run_uuid(),
                trace_id=TelemetryContext.get_trace_id(),
                span_id=TelemetryContext.get_current_span_id(),
                component="executor",
                action=marker,
                payload=payload,
            )
            recorder.record_event(event)
            if flush:
                recorder.flush()

    def _mark_progress(
        self,
        marker: str,
        *,
        run: Any = None,
        step: Optional[str] = None,
        elapsed_s: Optional[float] = None,
        level: str = "debug",
        extra: Optional[dict[str, Any]] = None,
        flush: bool = False,
    ) -> None:
        if not self._diagnostic_instrumentation_enabled():
            return

        self._last_progress_marker = marker
        self._last_progress_timestamp = time.time()
        self._record_execution_event(
            marker,
            run=run,
            step=step,
            elapsed_s=elapsed_s,
            level=level,
            extra=extra,
            flush=flush,
        )

    def _heartbeat_progress(
        self,
        label: str,
        *,
        started_at: float,
        iteration: int,
        run: Any = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        if not self._diagnostic_instrumentation_enabled():
            return

        now = time.time()
        last_emit = self._loop_heartbeat_timestamps.get(label, 0.0)
        if now - last_emit >= self.diagnostic_progress_interval:
            payload = {"iteration": iteration, "wait_started_at": started_at}
            if extra:
                payload.update(extra)
            self._mark_progress(
                "{}.heartbeat".format(label),
                run=run,
                elapsed_s=now - started_at,
                extra=payload,
            )
            self._loop_heartbeat_timestamps[label] = now

        self._maybe_emit_stall_snapshot(
            label,
            run=run,
            elapsed_s=now - started_at,
            extra=extra,
        )

    def _maybe_emit_stall_snapshot(
        self,
        label: str,
        *,
        run: Any = None,
        elapsed_s: Optional[float] = None,
        extra: Optional[dict[str, Any]] = None,
        force: bool = False,
    ) -> None:
        if not self._diagnostic_instrumentation_enabled():
            return

        now = time.time()
        if not force:
            if not self._last_progress_timestamp:
                return
            if now - self._last_progress_timestamp < self.diagnostic_stall_timeout:
                return
            if now - self._last_stall_warning_timestamp < self.diagnostic_progress_interval:
                return

        payload = {
            "label": label,
            "last_progress_marker": self._last_progress_marker,
            "last_progress_age_s": (
                now - self._last_progress_timestamp if self._last_progress_timestamp else None
            ),
            "thread_name": current_thread().name,
            "last_device_io": get_last_device_io_snapshot(
                TelemetryContext.get_trace_id(), TelemetryContext.get_run_id()
            ),
        }
        if extra:
            payload.update(extra)

        self._last_stall_warning_timestamp = now
        self._record_execution_event(
            "{}.stall_snapshot".format(label),
            run=run,
            elapsed_s=elapsed_s,
            level="warning",
            event_type=EventType.STALL_SNAPSHOT.value,
            extra=payload,
            flush=True,
        )

    def _should_overlap_run(self, run, spec) -> bool:
        overlap_enabled = bool(spec.overlap[0])
        return self._controller.should_queue_overlap(
            run_is_last=bool(run.is_last),
            analysis_type=str(run.spec.analysis_type),
            overlap_enabled=overlap_enabled,
        )

    def _run_execution_mode(self, run, spec) -> str:
        overlap_enabled = bool(spec.overlap[0])
        return self._controller.queue_run_execution_mode(
            run_is_last=bool(run.is_last),
            analysis_type=str(run.spec.analysis_type),
            overlap_enabled=overlap_enabled,
        )

    def _execute_run_overlap(
        self, exp: Any, run: Any, delay_after_previous_analysis: Any, con: Any
    ) -> bool:
        self._controller.mark_queue_overlap(True, queue_name=exp.name)
        t = None
        for action in self._controller.queue_overlap_launch_actions():
            if action == "wait_extracting":
                self.debug("waiting for extracting_run to finish")
                self._wait_for(lambda x: self.extracting_run)
            elif action == "start_overlap_thread":
                self.info("overlaping")
                self._mark_progress("run.overlap_thread_start", run=run)
                ctx = copy_context()
                t = Thread(
                    target=ctx.run,
                    args=(self._do_run, run, delay_after_previous_analysis),
                    name=run.runid,
                )
                t.start()
            elif action == "wait_overlap_signal":
                self._mark_progress("run.overlap_signal_wait.start", run=run)
                run.wait_for_overlap()
                self._mark_progress("run.overlap_signal_wait.end", run=run)
                self.debug("overlap finished. starting next run")

        if t is not None:
            con.add_consumable((t, run))
        return False

    def _execute_run_serial(
        self, exp: Any, spec: Any, run: Any, delay_after_previous_analysis: Any
    ) -> bool:
        self._controller.mark_queue_overlap(False, queue_name=exp.name)
        self._join_run(spec, run, delay_after_previous_analysis)
        return True

    def _settle_active_runs(self) -> None:
        actions = self._controller.queue_settle_actions(
            has_extracting_run=bool(self.extracting_run),
            extracting_is_special=bool(
                self.extracting_run and self.extracting_run.spec.is_special()
            ),
            has_measuring_run=bool(self.measuring_run),
        )
        self.debug("settling active runs actions={}".format(actions))
        self._mark_progress("queue.settle.start", extra={"actions": actions})
        for action in actions:
            self._mark_progress("queue.settle.action", extra={"action": action})
            if action == "wait_extracting":
                self._wait_for(lambda x: self.extracting_run)
            elif action == "cancel_special_extracting" and self.extracting_run:
                self.extracting_run.cancel_run()
            elif action == "wait_measuring":
                self._wait_for(lambda x: self.measuring_run)
            elif action == "wait_active_runs":
                self._wait_for(lambda x: self.extracting_run or self.measuring_run)
        self._mark_progress("queue.settle.end", extra={"actions": actions})

    def _get_run_subject_id(self, run: Any) -> str:
        subject_id = getattr(run, "uuid", None) or getattr(run, "runid", "unknown-run")
        return str(subject_id)

    def _transition_run_failure(self, run, reason: str) -> None:
        run_id = self._get_run_subject_id(run)
        machine = self._controller.get_run_machine(run_id)
        if machine is None:
            return

        event = None
        state = machine.observed_state
        if state == "run_starting":
            event = RUN_PRECHECK_FAILED
        elif state in ("run_precheck", "run_extracting", "run_waiting_overlap_signal"):
            event = EXTRACTION_FAILED
        elif state in ("run_waiting_min_pumptime", "run_measuring"):
            event = MEASUREMENT_FAILED
        elif state == "run_post_measurement":
            event = POST_MEASUREMENT_FAILED
        elif state == "run_saving":
            event = SAVE_FAILED
        elif state == "run_finishing":
            event = ABORT if self._aborted else CANCEL

        if event:
            if event == ABORT:
                self._controller.abort_run(run_id, reason=reason)
            elif event == CANCEL:
                self._controller.cancel_run(run_id, reason=reason)
            elif event == RUN_PRECHECK_FAILED:
                self._controller.mark_run_started(run_id, failed=True)
            elif event == EXTRACTION_FAILED:
                self._controller.complete_run_extraction(run_id, failed=True, reason=reason)
            elif event == MEASUREMENT_FAILED:
                self._controller.complete_run_measurement(run_id, failed=True, reason=reason)
            elif event == POST_MEASUREMENT_FAILED:
                self._controller.complete_run_post_measurement(run_id, failed=True, reason=reason)
            elif event == SAVE_FAILED:
                self._controller.complete_run_save(
                    run_id, queue_name=self.experiment_queue.name, failed=True, reason=reason
                )

    @on_trait_change("end_at_run_completion")
    def _handle_end_at_run_completion_change(self, new):
        if hasattr(self, "_controller"):
            self._controller.end_at_run_completion = bool(new)

    def set_managers(self, prog=None):
        p1 = "pychron.extraction_line.extraction_line_manager.ExtractionLineManager"
        p2 = "pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager"
        p3 = "pychron.spectrometer.ion_optics.ion_optics_manager.IonOpticsManager"
        if self.application:
            if prog:
                prog.change_message("Setting Spectrometer")
            self.spectrometer_manager = self.application.get_service(p2)
            if self.spectrometer_manager is None:
                if not globalv.ignore_plugin_warnings:
                    self.warning_dialog("Spectrometer Plugin is required for Experiment")
                    return
            self.ion_optics_manager = self.application.get_service(p3)

            if prog:
                prog.change_message("Setting Extraction Line")
            self.extraction_line_manager = self.application.get_service(p1)
            if self.extraction_line_manager is None:
                if not globalv.ignore_plugin_warnings:
                    self.warning_dialog("Extraction Line Plugin is required for Experiment")
                    return

        dh = self.datahub
        dh.mainstore = self.application.get_service(DVC_PROTOCOL)
        dh.mainstore.precedence = 1

        return True

    def _initialize_watchdog(self) -> bool:
        """Initialize watchdog integration for device/service health monitoring.

        This is called after set_managers() to set up the watchdog system for
        pre-phase health checks. Should only be called once at executor startup.

        Returns:
            True if watchdog initialized successfully or disabled, False on error
        """
        try:
            from pychron.experiment.executor_watchdog_integration import (
                ExecutorWatchdogIntegration,
            )

            self._watchdog_integration = ExecutorWatchdogIntegration(self)
            return self._watchdog_integration.initialize_watchdog_system()
        except Exception as e:
            self.warning(f"Failed to initialize watchdog: {e}")
            self.debug_exception()
            return False

    @property
    def watchdog(self) -> "ExecutorWatchdogIntegration":
        """Get watchdog integration instance (lazy-initialize if needed).

        Returns:
            ExecutorWatchdogIntegration instance (or None if disabled/failed)
        """
        if self._watchdog_integration is None:
            self._initialize_watchdog()
        return self._watchdog_integration

    def bind_preferences(self):
        self.datahub.bind_preferences()

        prefid = "pychron.experiment"

        attrs = (
            "use_auto_save",
            "use_autoplot",
            "auto_save_delay",
            "min_ms_pumptime",
            "set_integration_time_on_start",
            "send_config_before_run",
            "verify_spectrometer_configuration",
            "default_integration_time",
            "use_xls_persistence",
            "use_db_persistence",
            "experiment_type",
            "ratio_change_detection_enabled",
            "use_preceding_blank",
            "execute_open_queues",
            "save_all_runs",
        )
        self._preference_binder(prefid, attrs)

        # dvc
        self._preference_binder(
            "pychron.dvc.experiment",
            ("use_dvc_persistence", "dvc_save_timeout_minutes", "use_dvc_overlap_save"),
        )

        # dashboard
        self._preference_binder("pychron.dashboard.experiment", ("use_dashboard_client",))

        # colors
        attrs = ("signal_color", "sniff_color", "baseline_color")
        self._preference_binder(prefid, attrs, mod="color")

        # user_notifier
        # attrs = ('include_log',)
        # self._preference_binder(prefid, attrs, obj=self.user_notifier)
        #
        # emailer = self.application.get_service('pychron.social.email.emailer.Emailer')
        # self.user_notifier.emailer = emailer

        # memory
        attrs = ("use_memory_check", "memory_threshold")
        self._preference_binder(prefid, attrs)

        # console
        self.console_bind_preferences(prefid)
        self._preference_binder(prefid, ("use_message_colormapping",))

        # general
        self._preference_binder("pychron.general", ("default_principal_investigator", "laboratory"))

    def add_event(self, *events):
        self.events.extend(events)

    def execute(self):
        if self._controller.should_reset_before_execute():
            self._controller.reset()
            self._sync_compatibility_state()
        elif not self._controller.can_execute():
            self.debug(
                "execute ignored because controller is not ready. state={}".format(
                    self._controller.executor_machine.observed_state
                )
            )
            return None

        self._controller.execute()
        prog = open_progress(100, position=(100, 100))

        pre_execute_result = False
        try:
            pre_execute_result = self._pre_execute_check(prog)
        except PreExecuteCheckException as e:
            self.warning_dialog(str(e))

        # if self._pre_execute_check(prog):
        if pre_execute_result:
            self.info("pre execute check successful")
            self._controller.precheck_passed()
            prog.close()
            # reset executor runtime context but preserve state-machine progress
            self._reset(reset_controller=False)

            t = Thread(name="Execute Queues", target=self._execute)
            t.start()
            return t
        else:
            self._controller.precheck_failed(reason="pre execute check failed")
            self._set_executor_terminal_result("failed", reason="pre execute check failed")
            prog.close()
            self.alive = False
            self.info("pre execute check failed")

    def set_queue_modified(self, queue=None):
        self.queue_modified = True
        self.stats.refresh_on_queue_change()
        queue = queue or self.experiment_queue
        if queue is not None:
            if hasattr(queue, "request_table_refresh"):
                queue.request_table_refresh()
            else:
                # Safely set trait from worker thread
                invoke_in_main_thread(setattr, queue, "refresh_table_needed", True)

            if hasattr(queue, "request_info_refresh"):
                queue.request_info_refresh()
            else:
                # Safely set trait from worker thread
                invoke_in_main_thread(setattr, queue, "refresh_info_needed", True)

    def sync_active_context(self, editor=None, queue=None, queues=None):
        if editor is not None:
            self.active_editor = editor

        if queue is None and editor is not None:
            queue = getattr(editor, "queue", None)

        if queue is not None:
            self.experiment_queue = queue
            selected = getattr(queue, "selected", None)
            self.selected_run = selected[0] if selected else None
            # Reset controller state machine when a new experiment is opened
            self.debug(f"sync_active_context: opening queue={queue.name}")
            self._controller.reset()
            # When user opens an experiment, assume it's executable
            # (it will be set to False by validation if there are errors)
            is_executable = True
            self.debug(f"sync_active_context: opened queue is_executable={is_executable}, controller.is_alive={self._controller.is_alive}")
            # Set both executable and sync state together to ensure Property recalculates
            self._set_ui_traits(
                executable=is_executable,
                alive=self._controller.is_alive,
                measuring=self._controller.measuring,
                extracting=self._controller.extracting,
                end_at_run_completion=self._controller.end_at_run_completion,
            )
            self.debug(f"sync_active_context: after traits - executable={self.executable}, alive={self.alive}, can_start={self.can_start}")
        elif editor is None:
            self.experiment_queue = None
            self.selected_run = None
            self._controller.reset()
            self._set_ui_traits(
                executable=False,
                alive=self._controller.is_alive,
                measuring=self._controller.measuring,
                extracting=self._controller.extracting,
                end_at_run_completion=self._controller.end_at_run_completion,
            )

        if queues is not None:
            self.experiment_queues = list(queues)

    def is_alive(self):
        try:
            exc = self._exception_queue.get_nowait()
            self.warning("exception queue. {}".format(exc))
            if exc[0] == "NonFatal":
                if self.confirmation_dialog(
                    "{}\n\nDo you want to CANCEL the experiment?\n".format(exc[1]),
                    timeout_ret=False,
                    timeout=30,
                ):
                    return False
            else:
                self.critical("exception kills experiment queue")
                return False

        except Empty:
            return self._controller.is_alive

    def continued(self):
        self.stats.continue_run()

    def cancel(self, *args, **kw):
        self._cancel(*args, **kw)

    def set_extract_state(self, state, flash=0.75, color="green", period=1.5):
        self._set_extract_state(state, flash, color, period)

    def wait(self, t, msg=""):
        self._wait(t, msg)

    def get_wait_control(self):
        with self.wait_control_lock:
            wd = self.wait_group.get_wait_control()
        return wd

    def stop(self):
        if self.delaying_between_runs:
            self._controller.request_stop_at_boundary()
            self.alive = False
            self.stats.stop_timer()
            self.wait_group.stop()

            msg = "{} Stopped".format(self.experiment_queue.name)
            self._set_message(msg, color="orange")

        self.cancel()

    def experiment_blob(self):
        path = self.experiment_queue.path
        path = add_extension(path, ".txt")
        if os.path.isfile(path):
            with open(path, "r") as rfile:
                return "{}\n{}".format(path, rfile.read())
        else:
            self.warning("{} is not a valid file".format(path))

    def show_conditionals(self, main_thread=True, *args, **kw):
        # if main_thread:
        #     invoke_in_main_thread(self._show_conditionals, *args, **kw)
        # else:
        #     self._show_conditionals(*args, **kw)
        self._show_conditionals(*args, **kw)

    def refresh_table(self, *args, **kw):
        self.experiment_queue.refresh_table_needed = True

    def abort_run(self):
        self.debug("abort run. Executor.isAlive={}".format(self.is_alive()))
        if self.is_alive():
            for crun, kind in (
                (self.measuring_run, "measuring"),
                (self.extracting_run, "extracting"),
            ):
                if crun:
                    self.debug("abort {} run {}".format(kind, crun.runid))
                    self._abort_run()
                    # do_after(50, self._cancel_run)
                    # t = Thread(target=self._cancel_run)
                    # t.start()
                    break

    def stop_run(self):
        self.debug("%%%%%%%%%%%%%%%%%% Stop fired alive={}".format(self.is_alive()))
        if self.is_alive():
            self.info("stop execution")
            self.stop()

    # ===============================================================================
    # private
    # ===============================================================================
    def _do_event(self, level, **kw):
        self.debug("doing event level: {}".format(level))
        ctx = self._make_event_context()
        ctx.update(**kw)
        for evt in self.events:
            # self.debug('Event {},{} '.format(evt.level, level))
            if evt.level == level:
                try:
                    evt.do(ctx)
                except BaseException as e:
                    self.warning("Event {} failed. exception: {}".format(evt.id, e))
                    import traceback

                    self.debug(traceback.format_exc())

    def _make_event_context(self, exp=None):
        if exp is None:
            exp = self.experiment_queue

        ctx = {
            "current_run_duration": self.stats.current_run_duration_f,
            "etf_iso": self.stats.etf_iso,
            "err_message": self._err_message,
            "canceled": self._should_cancel_execution(),
            "experiment_name": exp.name,
            "experiment": exp,
            "starttime": exp.start_timestamp,
            "username": exp.username,
            "use_email": exp.use_email,
            "use_group_email": exp.use_group_email,
            "user_email": exp.email,
            "group_emails": self._get_group_emails(exp.email),
            "mass_spectrometer": exp.mass_spectrometer,
        }
        return ctx

    def _reset(self, reset_controller=True):
        if reset_controller:
            self._controller.reset()
        self.alive = True
        self._canceled = False
        self._aborted = False

        self._err_message = ""
        self.end_at_run_completion = False
        self._controller.end_at_run_completion = False
        self.experiment_status.reset()
        self.experiment_queue.executed = True
        # scroll to the first run
        self.experiment_queue.automated_runs_scroll_to_row = 0
        self._sync_compatibility_state()

    def _wait_for_dvc_save(self, spec: Any) -> bool:
        if self.use_dvc_overlap_save and self._save_complete_evt and self.use_dvc_persistence:
            timeout = self.dvc_save_timeout_minutes
            self.debug("waiting for save event to clear. Timeout after {} minutes".format(timeout))
            timeoutseconds = timeout * 60
            st = time.time()
            iteration = 0
            self._mark_progress("run.save_wait.start", extra={"timeout_s": timeoutseconds})
            while self._save_complete_evt.is_set():
                self._save_complete_evt.wait(1)
                iteration += 1
                self._heartbeat_progress(
                    "run.save_wait",
                    started_at=st,
                    iteration=iteration,
                    extra={"timeout_s": timeoutseconds},
                )

                if time.time() - st > timeoutseconds:
                    self.warning_dialog("Saving run failed to complete success fully")
                    self._save_complete_evt.set()
                    # run.cancel_run()
                    spec.transition("fail", force=True, source="wait_for_overlap_save")
                    self._mark_progress(
                        "run.save_wait.timeout",
                        level="warning",
                        elapsed_s=time.time() - st,
                        extra={"timeout_s": timeoutseconds},
                        flush=True,
                    )
                    return

            self.debug("waiting complete")
            self._mark_progress("run.save_wait.end", elapsed_s=time.time() - st)

        return True

    def _wait_for_save(self) -> None:
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
            self.info("Waiting for save")
            cnt = 0
            self._mark_progress("queue.wait_for_save.start", extra={"auto_save_delay": delay})

            while not self.executable:
                time.sleep(1)
                cnt += 1
                self._heartbeat_progress(
                    "queue.wait_for_save",
                    started_at=st,
                    iteration=cnt,
                    extra={"auto_save_delay": delay, "executable": self.executable},
                )
                if time.time() - st < delay and self.is_alive():
                    self.set_extract_state(
                        "Waiting for save. Autosave in {} s".format(delay - cnt),
                        flash=False,
                    )
                else:
                    break

            if not self.executable:
                self.info("Timed out waiting for user input")
                if auto_save:
                    self.info("autosaving experiment queues")
                    self.set_extract_state("")
                    self.auto_save_event = True
                else:
                    self.info("canceling experiment queues")
                    self.cancel(confirm=False)
            self._mark_progress(
                "queue.wait_for_save.end",
                elapsed_s=time.time() - st,
                extra={"executable": self.executable},
            )

    def _execute(self) -> None:
        """
        execute opened experiment queues
        """
        exp = self.experiment_queue
        scheduler = self.scheduler

        name = exp.name

        if scheduler.delayed_start_enabled:
            t = scheduler.start_time
            tseconds = scheduler.get_startf()
            st = t.strftime("%a %H:%M")
            self.heading('Waiting until {} to start "{}"'.format(st, name))
            self.set_extract_state("scheduled start {}".format(st), flash=False)
            while 1:
                if self._should_cancel_execution() or not self._controller.is_alive:
                    return
                if time.time() > tseconds:
                    break
                time.sleep(1)
            self.set_extract_state(False)
        else:
            msg = 'Starting Execution "{}"'.format(name)
            self.heading(msg)

        # delay before starting
        self._delay(exp.delay_before_analyses, message="before")

        # Record session start
        _session_id = None
        _recorder = self._controller.telemetry_recorder
        set_global_recorder(_recorder)
        if _recorder is not None:
            _session_id = f"session_{int(time.time())}"
            _recorder.record_event(
                TelemetryEvent(
                    event_type=EventType.TELEMETRY_SESSION_START.value,
                    ts=time.time(),
                    level="info",
                    component="executor",
                    action="session_start",
                    payload={
                        "session_id": _session_id,
                        "total_queues": len(self.experiment_queues),
                    },
                )
            )

        try:
            self._mark_progress(
                "executor.session.start", extra={"session_id": _session_id}, flush=True
            )
            for i, exp in enumerate(self.experiment_queues):
                self._controller.queue_selected(queue_name=exp.name)
                self._set_thread_name(exp.name)
                self.heading('"{}" started'.format(exp.name))
                if self.is_alive():
                    if self._pre_queue_check(exp):
                        self.debug("pre queue check failed for {}".format(exp.name))
                        self._controller.run_failure(reason="pre queue check failed")
                        break

                    self._execute_queue(i, exp)
                else:
                    self.debug("Not alive. not starting {},{}".format(i, exp.name))

                if self._should_stop_at_boundary():
                    self.debug(
                        "Previous queue ended at completion. Not continuing to other opened experiments"
                    )
                    break

                if not self.execute_open_queues:
                    self.debug("Execute open queues preference not selected")
                    break

            # Record session end
            if _recorder is not None and _session_id is not None:
                _recorder.record_event(
                    TelemetryEvent(
                        event_type=EventType.TELEMETRY_SESSION_END.value,
                        ts=time.time(),
                        level="info",
                        component="executor",
                        action="session_end",
                        payload={
                            "session_id": _session_id,
                            "total_queues": len(self.experiment_queues),
                        },
                    )
                )

            self._set_executor_terminal_result(
                self._current_terminal_result(), reason=self._err_message or None
            )
            self.alive = False
        finally:
            self._maybe_emit_stall_snapshot("executor.session.end", force=True)
            # CRITICAL: Always close recorder on exit
            set_global_recorder(None)
            self._controller.close_session()

    def _execute_queue(self, i: int, exp: Any) -> None:
        """
        i: int
        exp: ExperimentQueue

        execute experiment queue ``exp``
        """

        self.experiment_queue = exp
        self._controller.begin_queue(exp.name)

        # Set up queue-level telemetry context
        if self._controller.telemetry_context:
            queue_name = exp.name
            trace_id = f"queue_{queue_name}_{int(time.time())}"
            TelemetryContext.set_queue_id(queue_name)
            TelemetryContext.set_trace_id(trace_id)

        self.info("Starting automated runs set={:02d} {}".format(i, exp.name))
        self._mark_progress(
            "queue.start", extra={"queue_index": i, "queue_name": exp.name}, flush=True
        )
        self.debug("reset stats: {}".format(self.stats))

        self.stats.experiment_queues = self.experiment_queues
        self.stats.active_queue = exp
        self.stats.reset()
        self.stats.start_timer()

        exp.start_timestamp = datetime.now()
        self._controller.start_delay_complete(queue_name=exp.name)

        self._save_complete_evt.clear()

        self._do_event(events.START_QUEUE)

        # save experiment to database
        # self.info('saving experiment "{}" to database'.format(exp.name))

        exp.n_executed_display = int(
            self.application.preferences.get("pychron.experiment.n_executed_display", 5)
        )

        # reset conditionals result file
        reset_conditional_results()

        last_runid = None

        rgen, nruns = exp.new_runs_generator()

        # Record queue start lifecycle event
        experiment_lifecycle.record_queue_started(exp.name, num_runs=nruns)

        cnt = 0
        total_cnt = 0
        is_first_flag = True
        is_first_analysis = True
        delay_after_previous_analysis = None
        # from pympler import classtracker
        # tr = classtracker.ClassTracker()
        # from pychron.experiment.automated_run.automated_run import AutomatedRun
        # tr.track_class(AutomatedRun)
        # tr.track_class(AutomatedRunPersister)
        # tr.create_snapshot()
        # self.tracker = tr

        with consumable(func=self._overlapped_run) as con:
            while 1:
                if not self.is_alive():
                    self.debug("executor not alive")
                    break

                if self.queue_modified:
                    self.debug("Queue modified. making new run generator")
                    rgen, nruns = exp.new_runs_generator()
                    cnt = 0
                    self.queue_modified = False

                try:
                    spec = next(rgen)
                except StopIteration:
                    self.debug("stop iteration")
                    self._controller.queue_empty(queue_name=exp.name)
                    break

                if spec.skip:
                    self.debug("caught a skipped run {}".format(spec.runid))
                    continue

                if self._check_scheduled_stop(spec):
                    self.info("Experiment scheduled to stop")
                    self._controller.stop_boundary_reached(queue_name=exp.name)
                    break

                if self._pre_run_check(spec):
                    self.warning("pre run check failed")
                    self._controller.run_failure(reason="pre run check failed")
                    break

                self._aborted = self._should_abort_execution()
                self.ms_pumptime_start = None
                # overlapping = self.current_run and self.current_run.isAlive()
                overlapping = bool(self.measuring_run and self.measuring_run.is_alive())
                if not overlapping:
                    if self.is_alive() and cnt < nruns and not is_first_analysis:
                        # delay between runs
                        self._delay(delay_after_previous_analysis)

                        if not self.is_alive():
                            self.debug("User Cancel between runs")
                            break

                    else:
                        self.debug(
                            "not delaying between runs isAlive={}, "
                            "cnts<nruns={}, is_first_analysis={}".format(
                                self.is_alive(), cnt < nruns, is_first_analysis
                            )
                        )

                if not self._wait_for_dvc_save(spec):
                    self.debug("wait for dvc save failed")
                    self._controller.run_failure(reason="wait for dvc save failed")
                    break

                self._controller.prepare_next_run(queue_name=exp.name)
                run = self._make_run(spec)
                if run is None:
                    self.debug("failed to make run")
                    self._controller.run_failure(reason="failed to make run")
                    break

                self.wait_group.set_active_page_name(run.runid)
                run.is_first = is_first_flag

                delay_after_previous_analysis = run.spec.get_delay_after(
                    exp.delay_between_analyses,
                    exp.delay_after_blank,
                    exp.delay_after_air,
                )
                if exp.delay_after_conditional:
                    # calculate conditional delay
                    conditional_delay = 0
                    delay_after_previous_analysis = max(
                        delay_after_previous_analysis, conditional_delay
                    )

                execution_mode = self._run_execution_mode(run, spec)
                if execution_mode == "overlap":
                    is_first_flag = self._execute_run_overlap(
                        exp, run, delay_after_previous_analysis, con
                    )
                else:
                    is_first_flag = self._execute_run_serial(
                        exp, spec, run, delay_after_previous_analysis
                    )
                    last_runid = run.runid

                # self.tracker.stats.print_summary()

                cnt += 1
                total_cnt += 1
                is_first_analysis = False
                if self._should_stop_at_boundary():
                    self.debug("end at run completion")
                    break

                # if spec.state in ("success", "truncated"):
                #     if self._ratio_change_detection(spec):
                #         self.warning("Ratio Change Detected")
                #         break

            self.debug(
                "run loop exited. end at completion:{}".format(self._should_stop_at_boundary())
            )
            self._settle_active_runs()

        if self._err_message:
            self.warning("automated runs did not complete successfully")
            self.warning("error: {}".format(self._err_message))

        self._end_runs()
        qresult = self._current_terminal_result()
        self._controller.finish_queue(
            qresult, queue_name=exp.name, reason=self._err_message or None
        )
        if last_runid:
            self.info("Automated runs ended at {}, runs executed={}".format(last_runid, total_cnt))

        self.heading("experiment queue {} finished".format(exp.name))
        self._mark_progress(
            "queue.end",
            level="info",
            extra={"queue_name": exp.name, "result": qresult, "error": self._err_message or None},
            flush=True,
        )

        if not self._err_message and self._should_stop_at_boundary():
            self._err_message = "User terminated"

        self._do_event(events.END_QUEUE)

        # Record queue end lifecycle event
        # Map qresult to status string (qresult is one of QUEUE_COMPLETED, QUEUE_FAILED, QUEUE_CANCELED, QUEUE_ABORTED)
        status_map = {
            QUEUE_COMPLETED: "success",
            QUEUE_FAILED: "failed",
            QUEUE_CANCELED: "canceled",
            QUEUE_ABORTED: "aborted",
        }
        status = status_map.get(qresult, "unknown")
        experiment_lifecycle.record_queue_completed(exp.name, status=status)

    def _get_group_emails(self, email):
        names, addrs = None, None
        path = os.path.join(paths.setup_dir, "users.yaml")
        if os.path.isfile(path):
            yl = yload(path)
            if yl:
                items = [
                    (i["name"], i["email"]) for i in yl if i["enabled"] and i["email"] != email
                ]

                if items:
                    names, addrs = list(zip(*items))
        return names, addrs

    def _wait_for(
        self, predicate: Callable[[float], Any], period: float = 1, invert: bool = False
    ) -> None:
        """
        predicate: callable. func(x)
        period: evaluate predicate every ``period`` seconds
        invert: bool invert predicate logic

        wait until predicate evaluates to False
        if invert is True wait until predicate evaluates to True
        """
        self.debug("waiting for")
        st = time.time()

        def finvert(func):
            def wrapper(x):
                return not func(x)

            return wrapper

        if invert:
            predicate = finvert(predicate)

        iteration = 0
        while 1:
            et = time.time() - st
            if not self._controller.is_alive:
                break

            v = predicate(et)
            if invert:
                v = not v

            if not v:
                break
            iteration += 1
            self._heartbeat_progress(
                "executor.wait_for",
                started_at=st,
                iteration=iteration,
                extra={"invert": invert, "predicate_result": bool(v)},
            )
            time.sleep(period)

    def _set_thread_name(self, name: str) -> None:
        self.debug("Changing Thread name to {}".format(name))
        ct = current_thread()
        ct.name = name

    def _join_run(self, spec: Any, run: Any, delay_after_run: Any) -> None:
        self.debug("join run")
        self._mark_progress("run.join.start", run=run)
        self._do_run(run, delay_after_run)

        self.debug("{} finished".format(run.runid))
        if self.is_alive():
            self.debug("spec analysis type {}".format(spec.analysis_type))
            self._set_prev(run)

        run.teardown()

        self.measuring_run = None
        self.debug("join run finished")
        self._mark_progress("run.join.end", run=run)

    def _set_prev(self, run):
        if hasattr(run, "get_baseline_corrected_signal_dict"):
            d = (run.record_id, run.get_baseline_corrected_signal_dict())
            if self.use_preceding_blank:
                self._prev_blanks[run.analysis_type] = d
                self._prev_blanks["blank"] = d
            self._prev_baselines = run.get_baseline_dict()
        else:
            at = run.spec.analysis_type
            if self.use_preceding_blank and at.startswith("blank"):
                pb = run.get_baseline_corrected_signals()
                if pb is not None:
                    d = (run.spec.runid, pb)
                    self._prev_blanks[at] = d
                    self._prev_blanks["blank"] = d
                    self.debug("previous blanks ={}".format(d))

            self._prev_baselines = run.get_baselines()

    def _do_run(self, run: Any, delay_after_run: Any) -> None:
        self._set_thread_name(run.runid)
        run_id = self._get_run_subject_id(run)
        self._controller.begin_run(run_id, queue_name=self.experiment_queue.name)

        # Set up run-level telemetry context
        ctx: TelemetryContext | None = None
        run_span_id: str | None = None
        if self._controller.telemetry_context:
            ctx = self._controller.telemetry_context
            TelemetryContext.set_run_id(run.runid)
            TelemetryContext.set_run_uuid(str(run.uuid))

        # add a new log handler

        name = run.runid.replace(":", "_")
        p, _ = unique_path2(paths.log_dir, name, extension=".log")
        handler = add_root_handler(p)
        run.log_path = p

        st = time.time()

        self.debug("do run")
        self._mark_progress("run.start", run=run, flush=True)

        self.stats.start_run(run)

        self._do_event(events.START_RUN)
        run.spec.transition("reset", force=True, source="execute_run")

        q = self.experiment_queue
        # is this the last run in the queue. queue is not empty until _start runs so n==1 means last run
        run.is_last = len(q.cleaned_automated_runs) == 1

        self.extracting_run = run

        # self.debug("parallel saving currently disabled")
        # if self._save_complete_evt and self.use_dvc_persistence:
        #     self.debug("waiting for save event to clear")
        #     st = time.time()
        #     while self._save_complete_evt.is_set():
        #         self._save_complete_evt.wait(1)
        #
        #         if time.time() - st > 300:
        #             self.warning_dialog("Saving run failed to complete success fully")
        #             self._save_complete_evt.set()
        #             run.cancel_run()
        #             run.spec.state = FAILED
        #             return
        #
        #     self.debug("waiting complete")

        try:
            for step in self._controller.run_step_sequence():
                step_name = step[1:]
                self._mark_progress(
                    "run.step.enter",
                    run=run,
                    step=step_name,
                    elapsed_s=time.time() - st,
                )
                run_status = self._controller.should_continue_run(
                    alive=self.is_alive(),
                    aborting=self._should_abort_execution(),
                    fatal_error=bool(self.monitor and self.monitor.has_fatal_error()),
                )
                if run_status == "stop":
                    self._mark_progress(
                        "run.step.stop", run=run, step=step_name, elapsed_s=time.time() - st
                    )
                    break

                if run_status == "abort":
                    self._controller.abort_run(run_id, reason="executor abort requested")
                    self._mark_progress(
                        "run.step.abort_requested",
                        run=run,
                        step=step_name,
                        elapsed_s=time.time() - st,
                    )
                    break

                if run_status == "fatal":
                    run.cancel_run()
                    run.spec.transition("fail", force=True, source="execute_run")
                    self._transition_run_failure(run, "fatal monitor error")
                    self._mark_progress(
                        "run.step.fatal_monitor",
                        run=run,
                        step=step_name,
                        elapsed_s=time.time() - st,
                    )
                    break

                if not getattr(self, step)(run):
                    self.warning("{} did not complete successfully".format(step[1:]))
                    self._controller.handle_run_step_failure(
                        run_id, step, reason="{} failed".format(step[1:])
                    )
                    if step != "_post_measurement":  # save data even if post measurement fails
                        run.spec.transition("fail", force=True, source="execute_run")
                    self._mark_progress(
                        "run.step.exit",
                        run=run,
                        step=step_name,
                        elapsed_s=time.time() - st,
                        level="warning",
                        extra={"completed": False},
                    )
                    break
                self._mark_progress(
                    "run.step.exit",
                    run=run,
                    step=step_name,
                    elapsed_s=time.time() - st,
                    extra={"completed": True},
                )

            else:
                self.debug("$$$$$$$$$$$$$$$$$$$$ state at run end {}".format(run.spec.state))
                if run.spec.state not in (TRUNCATED, CANCELED, FAILED):
                    run.spec.transition("complete", source="execute_run")

            self._mark_progress("run.save.enter", run=run, elapsed_s=time.time() - st)
            self._do_event(events.SAVE_RUN, run=run)
            self._controller.start_run_save(run_id, queue_name=self.experiment_queue.name)

            if not self._check_device_health_or_fail("measurement", run=run, context="before save"):
                return
            self._warn_on_service_health("save")

            if self._controller.should_save_run(run.spec.state, self.save_all_runs):
                kw = {}
                if self.use_dvc_overlap_save:
                    # run.save is non-blocked when exception queue defined
                    kw["exception_queue"] = self._exception_queue
                    kw["complete_event"] = self._save_complete_evt

                run.save(**kw)

            self._save_complete_evt.set()
            self._controller.complete_run_save(run_id, queue_name=self.experiment_queue.name)
            self._mark_progress("run.save.exit", run=run, elapsed_s=time.time() - st)
            t = time.time() - st
            for action in self._controller.run_post_save_actions(
                run_state=str(run.spec.state),
                use_autoplot=bool(self.use_autoplot),
                experiment_type=str(self.experiment_type),
            ):
                if action == "set_run_completed":
                    self._set_ui_event("run_completed", run)
                elif action == "remove_backup":
                    remove_backup(run.uuid)
                elif action == "post_run_check":
                    if run.spec.state not in (CANCELED, FAILED):
                        if self._post_run_check(run):
                            self._err_message = "Post Run Check Failed"
                            self.warning("post run check failed")
                        else:
                            self.heading("Post Run Check Passed")
                            try:
                                self._update_timeseries()
                            except BaseException:
                                self.debug("failed updating timeseries via experiment")
                                self.debug_exception()
                elif action == "log_run_duration":
                    self.info(
                        "Automated run {} {} duration: {:0.3f} s".format(
                            run.runid, run.spec.state, t
                        )
                    )
                elif action == "finish_run":
                    run.finish()
                elif action == "update_arar_values":
                    run.spec.uage = run.isotope_group.uage
                    run.spec.k39 = run.isotope_group.get_computed_value("k39")
                elif action == "publish_autoplot":
                    self._set_ui_event("autoplot_event", run)
                elif action == "pop_wait_group":
                    self.wait_group.pop()
                elif action == "finish_stats_run":
                    self.stats.finish_run()
                elif action == "update_stats":
                    if run.spec.state == SUCCESS:
                        self.stats.update_run_duration(run, t)
                        self.stats.recalculate_etf()
                elif action == "write_queue_files":
                    self._write_rem_ex_experiment_queues()
                elif action == "end_run_event":
                    self._do_event(events.END_RUN, run=run, delay_after_run=delay_after_run)
                    # Record run completion lifecycle event
                    status_map = {
                        "success": "success",
                        "failed": "failed",
                        "canceled": "canceled",
                        "invalid": "invalid",
                    }
                    run_status = status_map.get(run.spec.state.lower(), run.spec.state.lower())
                    experiment_lifecycle.record_run_completed(
                        self.experiment_queue.name,
                        run_id,
                        status=run_status,
                    )
                elif action == "remove_root_handler":
                    remove_root_handler(handler)
                elif action == "post_finish":
                    run.post_finish()
                elif action == "remove_run_machine":
                    self._controller.remove_run_machine(run_id)
                elif action == "refresh_queue_table":
                    self._set_thread_name(self.experiment_queue.name)
                    self.experiment_queue.refresh_table_needed = True
        finally:
            self._mark_progress(
                "run.end",
                run=run,
                elapsed_s=time.time() - st,
                level="info",
                extra={"run_state": getattr(run.spec, "state", None)},
                flush=True,
            )
            # CRITICAL: Clear run context after run completes
            if ctx:
                ctx.set_run_id(None)
                ctx.set_run_uuid(None)

    def _close_cv(self):
        self.debug("close cv {}".format(self._cv_info))
        if self._cv_info:
            try:
                invoke_in_main_thread(self._cv_info.control.close)
            except (AttributeError, ValueError, TypeError) as e:
                self._cv_info = None
                self.critical("Failed closing conditionals view {}".format(e))
                # window could already be closed

    def _write_rem_ex_experiment_queues(self):
        self.debug("write rem/ex queues")
        q = self.experiment_queue
        for runs, tag in ((q.automated_runs, "rem"), (q.executed_runs, "ex")):
            path = os.path.join(paths.experiment_rem_dir, "{}.{}.txt".format(q.name, tag))
            self.debug(path)
            with open(path, "w") as wfile:
                q.dump(wfile, runs=runs)

    def _overlapped_run(self, v: Any) -> None:
        self._overlapping = True
        t, run = v
        # while t.is_alive():
        # time.sleep(1)
        self.debug("OVERLAPPING. waiting for run to finish")
        started_at = time.time()
        iteration = 0
        self._mark_progress("run.overlap_join.start", run=run)
        while t.is_alive():
            t.join(timeout=1.0)
            iteration += 1
            self._heartbeat_progress(
                "run.overlap_join",
                started_at=started_at,
                iteration=iteration,
                run=run,
            )

        self.debug("{} finished".format(run.runid))
        self._set_prev(run)
        # if run.analysis_type.startswith('blank'):
        #     pb = run.get_baseline_corrected_signals()
        #     if pb is not None:
        #         self._prev_blanks[run.spec.analysis_type] = (run.spec.runid, pb)
        #         self._prev_blanks['blank'] = (run.spec.runid, pb)

        invoke_in_main_thread(do_after, 1000, run.teardown)
        self._mark_progress("run.overlap_join.end", run=run, elapsed_s=time.time() - started_at)

    def _abort_run(self):
        self.debug("Abort Run")
        self._controller.request_abort()
        self.set_extract_state(False)
        self.wait_group.stop()

        self._aborted = True
        for arun in (self.measuring_run, self.extracting_run):
            if arun:
                arun.abort_run()

    def _cancel(self, style="queue", cancel_run=False, msg=None, confirm=True, err=None):
        self.debug(
            "_cancel. style={}, cancel_run={}, msg={}, confirm={}, err={}".format(
                style, cancel_run, msg, confirm, err
            )
        )
        aruns = (self.measuring_run, self.extracting_run)

        if style == "queue":
            name = os.path.basename(self.experiment_queue.path)
            name, _ = os.path.splitext(name)
        else:
            name = aruns[0].runid

        if name:
            ret = YES
            if confirm:
                m = '"{}" is in progress. Are you sure you want to cancel'.format(name)
                if msg:
                    m = "{}\n{}".format(m, msg)

                ret = self.confirmation_dialog(
                    m, title="Confirm Cancel", return_retval=True, timeout=30
                )

            if ret == YES:
                # stop queue
                if style == "queue":
                    self._controller.request_cancel()
                    self.alive = False
                    self.debug("Queue cancel. stop timer")
                    invoke_in_main_thread(self.stats.stop_timer)

                invoke_in_main_thread(self.set_extract_state, False)
                invoke_in_main_thread(self.wait_group.stop)

                self._canceled = True
                if style != "queue":
                    self._controller.request_cancel()
                for arun in aruns:
                    if arun:
                        if style == "queue":
                            state = None
                            if cancel_run:
                                state = "canceled"
                        else:
                            state = "canceled"
                            # arun.aliquot = 0

                        arun.cancel_run(state=state)

                # self.debug('&&&&&&& Clearing runs')
                # self.measuring_run = None
                # self.extracting_run = None
                if err is None:
                    err = "User Canceled"
                self._err_message = err

    def _end_runs(self):
        self.debug("End Runs. stats={}".format(self.stats))
        for action in self._controller.queue_completion_actions():
            if action == "stop_stats_timer":
                self.stats.stop_timer()
            elif action == "clear_extract_state":
                self.set_extract_state(False)
            elif action == "set_queue_message":
                msg, color = self._controller.queue_completion_message(
                    queue_name=self.experiment_queue.name,
                    stop_at_boundary=self._should_stop_at_boundary(),
                    canceled=self._should_cancel_execution(),
                )
                self._set_message(msg, color)
            elif action == "sync_compatibility_state":
                self._sync_compatibility_state()

    def _show_conditionals(self, active_run=None, tripped=None, conditionals=None, kind="live"):
        try:
            v = ConditionalsView()

            self.debug("Show conditionals active run: {}".format(active_run))
            self.debug("Show conditionals measuring run: {}".format(self.measuring_run))
            self.debug(
                "active_run same as measuring_run: {}".format(self.measuring_run == active_run)
            )
            if active_run:
                if conditionals:
                    cd = conditionals
                else:
                    cd = {
                        "{}s".format(tag): getattr(active_run, "{}_conditionals".format(tag))
                        for tag in CONDITIONAL_GROUP_TAGS
                    }

                v.add_conditionals(cd, level=RUN)
                v.title = "{} ({})".format(v.title, active_run.runid)
            else:
                run = self.selected_run
                if run:
                    # in this case run is an instance of AutomatedRunSpec
                    p = get_path(
                        paths.conditionals_dir,
                        self.selected_run.conditionals,
                        [".yaml", ".yml"],
                    )
                    if p:
                        v.add_conditionals(conditionals_from_file(p, level=RUN))

                    if run.aliquot:
                        runid = run.runid
                    else:
                        runid = run.identifier

                    if run.position:
                        id2 = "position={}".format(run.position)
                    else:
                        idx = self.active_editor.queue.automated_runs.index(run) + 1
                        id2 = "RowIdx={}".format(idx)

                    v.title = "{} ({}, {})".format(v.title, runid, id2)
                else:
                    v.add_pre_run_terminations(
                        self._load_system_conditionals("pre_run_terminations")
                    )
                    v.add_pre_run_terminations(
                        self._load_queue_conditionals("pre_run_terminations")
                    )

                    v.add_system_conditionals(self._load_system_conditionals(None))
                    v.add_conditionals(self._load_queue_conditionals(None))

                    v.add_post_run_terminations(
                        self._load_system_conditionals("post_run_terminations")
                    )
                    v.add_post_run_terminations(
                        self._load_queue_conditionals("post_run_terminations")
                    )

            if tripped:
                v.select_conditional(tripped, tripped=True)

            self.conditionals_view = v

            self._set_ui_event("show_conditionals_event")
            # self._close_cv()

            # self._cv_info = open_view(v, kind=kind)
            # self.debug('open view _cv_info={}'.format(self._cv_info))

        except BaseException:
            self.warning(
                "******** Exception trying to open conditionals. Notify developer ********"
            )
            self.debug_exception()

    # ===============================================================================
    # execution steps
    # ===============================================================================
    def _start(self, run: Any) -> bool:
        ret = True
        self._mark_progress("run.start_phase.enter", run=run)

        if self.set_integration_time_on_start:
            dit = self.default_integration_time
            self.info("Setting default integration. t={}".format(dit))
            run.set_integration_time(dit)

        if not run.start():
            self.alive = False
            ret = False
            run.spec.transition("fail", force=True, source="pre_execute_check")
            self._controller.mark_run_started(self._get_run_subject_id(run), failed=True)

            msg = "Run {} did not start properly".format(run.runid)
            self._err_message = msg
            self._canceled = True
            self._controller.request_cancel()
            self.information_dialog(msg)
        else:
            self.experiment_queue.set_run_inprogress(run.runid)
            self._controller.mark_run_started(
                run_id=self._get_run_subject_id(run),
                queue_name=self.experiment_queue.name,
            )

            # Record run start lifecycle event
            sample = getattr(run, "sample", None)
            material = getattr(run, "material", None)
            experiment_lifecycle.record_run_started(
                self.experiment_queue.name,
                self._get_run_subject_id(run),
                sample=sample,
                material=material,
            )

        self._mark_progress("run.start_phase.exit", run=run, extra={"completed": ret})
        return ret

    def _extraction(self, ai: Any) -> Any:
        """
        ai: AutomatedRun
        extraction step
        """
        with Span(
            component="executor",
            action="extraction",
        ):
            self._mark_progress("run.extraction.enter", run=ai)
            if self._pre_step_check(ai, "Extraction"):
                self._failed_execution_step("Pre Extraction Check Failed")
                return

            if not self._check_device_health_or_fail("extraction", run=ai):
                self._mark_progress("run.extraction.exit", run=ai, extra={"completed": False})
                return False
            self._warn_on_service_health("extraction")

            # make sure status monitor is running a
            self.extraction_line_manager.setup_status_monitor()
            syn_extractor = SynExtractionCollector(executor=self)
            self.extraction_line_manager.set_experiment_type(self.experiment_type)

            ret = True
            if ai.start_extraction():
                self._controller.start_run_extraction(self._get_run_subject_id(ai))
                # Record extraction start
                experiment_lifecycle.record_extraction_started(
                    self.experiment_queue.name,
                    self._get_run_subject_id(ai),
                )
                self._set_ui_traits(extracting=True)
                if not ai.do_extraction(syn_extractor):
                    self._controller.complete_run_extraction(
                        self._get_run_subject_id(ai), failed=True, reason="Extraction Failed"
                    )
                    # Record extraction failure
                    experiment_lifecycle.record_extraction_completed(
                        self.experiment_queue.name,
                        self._get_run_subject_id(ai),
                        status="failed",
                    )
                    ret = self._failed_execution_step("Extraction Failed")
                else:
                    self._controller.complete_run_extraction(self._get_run_subject_id(ai))
                    # Record extraction success
                    experiment_lifecycle.record_extraction_completed(
                        self.experiment_queue.name,
                        self._get_run_subject_id(ai),
                        status="success",
                    )
            else:
                ret = ai.is_alive()

            self._set_ui_traits(extracting=False)
            self.experiment_status.reset()
            self.extracting_run = None
            self._mark_progress("run.extraction.exit", run=ai, extra={"completed": ret})
            return ret

    def syn_measure(self, ai, script):
        return self._measurement(ai, script=script, use_post_on_fail=False)

    def _measurement(self, ai: Any, **measurement_kwargs: Any) -> Any:
        """
        ai: AutomatedRun
        measurement step
        """
        with Span(
            component="executor",
            action="measurement",
        ):
            self._mark_progress("run.measurement.enter", run=ai)
            if self._pre_step_check(ai, "Measurement"):
                self._failed_execution_step("Pre Measurement Check Failed")
                return

            if not self._check_device_health_or_fail("measurement", run=ai):
                self._mark_progress("run.measurement.exit", run=ai, extra={"completed": False})
                return False
            self._warn_on_service_health("measurement")

            if self.send_config_before_run:
                self.info("Sending spectrometer configuration")
                man = self.spectrometer_manager
                man.send_configuration()
                if self.verify_spectrometer_configuration:
                    if not man.verify_configuration():
                        ret = self._failed_execution_step(
                            "Setting Spectrometer Configuration Failed"
                        )
                        return ret

            ret = True
            self.measuring_run = ai
            if ai.start_measurement():
                self._controller.start_run_measurement(self._get_run_subject_id(ai))
                # Record measurement start
                experiment_lifecycle.record_measurement_started(
                    self.experiment_queue.name,
                    self._get_run_subject_id(ai),
                )
                # only set to measuring (e.g switch to iso evo pane) if
                # automated run has a measurement_script
                self._set_ui_traits(measuring=True)

                self._mark_progress("run.measurement.script.enter", run=ai)
                if not ai.do_measurement(**measurement_kwargs):
                    self._controller.complete_run_measurement(
                        self._get_run_subject_id(ai), failed=True, reason="Measurement Failed"
                    )
                    # Record measurement failure
                    experiment_lifecycle.record_measurement_completed(
                        self.experiment_queue.name,
                        self._get_run_subject_id(ai),
                        status="failed",
                    )
                    ret = self._failed_execution_step("Measurement Failed")
                else:
                    self._controller.complete_run_measurement(self._get_run_subject_id(ai))
                    # Record measurement success
                    experiment_lifecycle.record_measurement_completed(
                        self.experiment_queue.name,
                        self._get_run_subject_id(ai),
                        status="success",
                    )
                self._mark_progress("run.measurement.script.exit", run=ai, extra={"completed": ret})
            else:
                ret = ai.is_alive()

            self._set_ui_traits(measuring=False)
            self._mark_progress("run.measurement.exit", run=ai, extra={"completed": ret})
            return ret

    def _post_measurement(self, ai: Any) -> Optional[bool]:
        """
        ai: AutomatedRun
        post measurement step
        """
        self._mark_progress("run.post_measurement.enter", run=ai)
        self._controller.start_run_post_measurement(self._get_run_subject_id(ai))
        if not ai.do_post_measurement():
            self._controller.complete_run_post_measurement(
                self._get_run_subject_id(ai),
                failed=True,
                reason="Post Measurement Failed",
            )
            self._failed_execution_step("Post Measurement Failed")
        else:
            self._controller.complete_run_post_measurement(self._get_run_subject_id(ai))
            self._mark_progress("run.post_measurement.exit", run=ai, extra={"completed": True})
            return True
        self._mark_progress("run.post_measurement.exit", run=ai, extra={"completed": False})
        return None

    def _check_device_health_or_fail(
        self,
        phase_name: str,
        run: Any | None = None,
        context: str | None = None,
    ) -> bool:
        if not (self.watchdog and self.watchdog.enabled):
            return True

        try:
            passed, msg = self.watchdog.check_phase_device_health(phase_name)
            if not passed:
                prefix = context or phase_name
                return self._handle_device_communication_failure(f"{msg} ({prefix})", run=run)
            if msg and "degraded" in msg.lower():
                self.warning(f"Device health check: {msg}")
        except Exception as e:
            self.debug(f"Watchdog device health check error (continuing): {e}")
            self.debug_exception()

        return True

    def _warn_on_service_health(self, phase_name: str) -> None:
        if not (self.watchdog and self.watchdog.enabled):
            return

        try:
            _, msg = self.watchdog.check_phase_service_health(phase_name)
            if msg and "failed" in msg.lower():
                self.warning(f"Service health check before {phase_name}: {msg}")
        except Exception as e:
            self.debug(f"Watchdog service health check error before {phase_name} (continuing): {e}")
            self.debug_exception()

    def _handle_device_communication_failure(
        self,
        msg: str,
        run: Any | None = None,
    ) -> bool:
        self.warning(msg)
        self._err_message = msg
        self.set_extract_state(False)
        self.wait_group.stop()
        if run is not None:
            run.spec.transition("fail", force=True, source="device_communication_failure")
            self._transition_run_failure(run, msg)
        self._controller.run_failure(reason=msg)
        self.alive = False
        return False

    def _failed_execution_step(self, msg: str) -> bool:
        self.debug("failed execution step {}".format(msg))
        if not self._should_cancel_execution():
            self.heading(msg)
            self._err_message = msg
            self._controller.run_failure(reason=msg)
            self.alive = False
        return False

    # ===============================================================================
    # utilities
    # ===============================================================================
    def _make_run(self, spec):
        """
        spec: AutomatedRunSpec
        return AutomatedRun

        generate an AutomatedRun for this ``spec``.

        """
        exp = self.experiment_queue

        if not self._set_run_aliquot(spec):
            self._controller.invalidate_run(
                str(getattr(spec, "uuid", spec.runid)), reason="aliquot setup failed"
            )
            return

        run = None

        spec.apply_queue_metadata(exp, force=True)

        arun = spec.make_run(run=run)
        arun.logger_name = "AutomatedRun {}".format(arun.runid)

        if spec.end_after:
            self.end_at_run_completion = True
            self._controller.request_stop_at_boundary()
            arun.is_last = True

        """
            save this runs uuid to a hidden file
            used for analysis recovery
        """
        self._add_backup(arun.uuid)

        arun.integration_time = 1.04

        arun.labspy_client = self.application.get_service("pychron.labspy.client.LabspyClient")

        for k in (
            "signal_color",
            "sniff_color",
            "baseline_color",
            "ms_pumptime_start",
            "datahub",
            "console_display",
            "experiment_queue",
            "spectrometer_manager",
            "extraction_line_manager",
            "ion_optics_manager",
            "use_db_persistence",
            "use_dvc_persistence",
            "use_xls_persistence",
        ):
            setattr(arun, k, getattr(self, k))

        try:
            pb = self._prev_blanks[spec.analysis_type]
        except KeyError:
            pb = self._prev_blanks.get("blank", ("", {}))

        arun.previous_blanks = pb
        arun.previous_baselines = self._prev_baselines
        arun.on_trait_change(self._handle_executor_event, "executor_event")

        arun.set_preferences(self.application.preferences)

        arun.refresh_scripts()

        for sname in SCRIPT_NAMES:
            script = getattr(arun, sname)
            if script:
                script.application = self.application
                script.manager = self
                script.runner = self.pyscript_runner

        arun.extract_device = exp.extract_device
        arun.persister.datahub = self.datahub
        arun.persister.dbexperiment_identifier = exp.database_identifier

        arun.use_syn_extraction = True

        if self.use_dvc_persistence:
            dvcp = self.application.get_service("pychron.dvc.dvc_persister.DVCPersister")
            if dvcp:
                dvcp.load_name = exp.load_name
                dvcp.default_principal_investigator = self.default_principal_investigator
                arun.dvc_persister = dvcp

                repid = spec.repository_identifier
                self.datahub.mainstore.add_repository(
                    repid, self.default_principal_investigator, inform=False
                )

                arun.dvc_persister.initialize(repid)

        mon = self.monitor
        if mon is not None:
            # mon.automated_run = arun
            arun.monitor = mon
            arun.persister.monitor = mon

        if self.use_xls_persistence:
            xls_persister = ExcelPersister()
            xls_persister.load_name = exp.load_name
            if mon is not None:
                xls_persister.monitor = mon
            arun.xls_persister = xls_persister

        return arun

    def _set_run_aliquot(self, spec):
        """
        spec: AutomatedRunSpec

        set the aliquot/step for this ``spec``
        check for conflicts between primary and secondary databases

        """

        if spec.conflicts_checked:
            return True

        # if a run in executed runs is in extraction or measurement state
        # we are in overlap mode
        dh = self.datahub

        ens = self.experiment_queue.executed_runs
        step_offset, aliquot_offset = 0, 0

        exs = [ai for ai in ens if ai.state in EM_SCRIPT_KEYS]
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
        """
        handle databases in conflict
        """
        dh = self.datahub

        ret = self.confirmation_dialog(
            "Databases are in conflict. "
            "Do you want to modify the Run Identifier to {}".format(dh.new_runid),
            timeout_ret=True,
            timeout=30,
        )
        if ret:
            dh.update_spec(spec, aoffset, soffset)
            ret = True
            self._canceled = False
            self._err_message = ""
        else:
            spec.conflicts_checked = False
            self._canceled = True
            self._err_message = "Databases are in conflict. {}".format(conflict)
            self.message(self._err_message)

        if self._canceled:
            self.cancel()

        return ret

    def _delay(self, delay: Any, message: str = "between") -> None:
        """
        delay: float
        message: str

        sleep for ``delay`` seconds
        """
        if delay:
            self.delaying_between_runs = True
            msg = "Delay {} runs {} sec".format(message, delay)
            self.info(msg)
            self._mark_progress("executor.delay.start", extra={"delay": delay, "message": message})
            self._wait(delay, msg)
            self.delaying_between_runs = False
            self._mark_progress("executor.delay.end", extra={"delay": delay, "message": message})

    def _wait(self, delay: Any, msg: str) -> None:
        """
        delay: float
        message: str

        sleep for ``delay`` seconds using a WaitControl
        """
        wg = self.wait_group
        wc = self.get_wait_control()

        self.debug(
            "executor wait boundary run={} delay={} message={} wait_page={} controls={} thread={}".format(
                getattr(getattr(self, "measuring_run", None), "runid", None)
                or getattr(getattr(self, "extracting_run", None), "runid", None),
                delay,
                msg,
                getattr(wc, "page_name", None),
                len(getattr(wg, "controls", [])),
                current_thread().name,
            )
        )
        self._mark_progress("executor.wait.start", extra={"delay": delay, "message": msg})
        wg.start_wait(wc, duration=delay, message=msg)
        wg.pop(wc)
        self._mark_progress("executor.wait.end", extra={"delay": delay, "message": msg})

    def _set_extract_state(self, state, *args):
        """
        state: str
        """
        self.debug("set extraction state {} {}".format(state, args))
        if state:
            self.experiment_status.set_state(state, *args)
        else:
            self.experiment_status.end()

    def _add_backup(self, uuid_str):
        """
        add uuid to backup recovery file
        """

        with open(paths.backup_recovery_file, "a") as rfile:
            rfile.write("{}\n".format(uuid_str))

    # ===============================================================================
    # checks
    # ===============================================================================
    def _ratio_change_detection(self, spec):
        if self.ratio_change_detection_enabled:
            self.debug("check for significant changes in isotopic ratios")
            p = paths.ratio_change_detection
            if os.path.isfile(p):
                atype = spec.analysis_type
                ms = self.experiment_queue.mass_spectrometer
                try:
                    checks = yload(p)
                    if checks:
                        for ci in checks:
                            if self._check_ratio_change(ms, atype, ci):
                                return True
                except BaseException as e:
                    import traceback

                    traceback.print_exc()
                    self.debug("Invalid Ratio Change Detection file at {}. Error={}".format(p, e))

            else:
                self.warning(
                    "Ratio Change Detection enabled but no configuration file located at {}".format(
                        p
                    )
                )

    def _check_ratio_change(self, ms, atype, check):
        analysis_type = check["analysis_type"]
        mainstore = self.datahub.mainstore
        if atype == analysis_type:
            ratio_name = check["ratio"]
            threshold = check.get("threshold", 0)
            nsigma = check.get("nsigma", 0)
            failure_cnt = check.get("failure_count", 1)
            consecutive_failure = check.get("consecutive_failure", True)
            nominal_ratio = check.get("nominal_ratio")
            nanalyses = check["nanalyses"] + 1
            pthreshold = check.get("percent_threshold", 0)
            mswd_threshold = check.get("mswd_threshold", 0)
            send_email_only = check.get("send_email_only", False)

            if not threshold and not nsigma:
                self.warning(
                    "invalid ratio change check. need to specify either threshold or nsigma"
                )
                return

            if nominal_ratio and not (threshold or pthreshold):
                self.warning(
                    "invalid ratio change check. need to specify either threshold or percent_threshold when "
                    'using "nominal_ratio"'
                )
                return

            self.debug("checking ratio change for {}. Ratio={}".format(analysis_type, ratio_name))

            self.debug("retrieved analyses")
            if nominal_ratio:
                ans = mainstore.get_last_n_analyses(
                    1, mass_spectrometer=ms, analysis_types=atype, verbose=False
                )
                ans = mainstore.make_analyses(ans, use_progress=False)
            else:
                ratios = self._ratios.get(atype, [])
                nn = max(nanalyses - len(ratios), 1)

                excluded = self._excluded_uuids.get(atype, [])
                with mainstore.session_ctx(use_parent_session=True):
                    ans = mainstore.get_last_n_analyses(
                        nn,
                        mass_spectrometer=ms,
                        analysis_types=atype,
                        excluded_uuids=excluded,
                        verbose=False,
                    )
                    ans = mainstore.make_analyses(ans, use_progress=False)

            rs = ((ai.uuid, ai.record_id, ai.get_ratio(ratio_name)) for ai in ans)
            ratios += reversed([ri for ri in rs if ri[2] is not None])
            if nominal_ratio:
                cur = nominal_value(ratios[-1][2])

                dev = abs(cur - nominal_ratio)
                if pthreshold:
                    dev = (dev / nominal_ratio) * 100
                    threshold = pthreshold
                msg = "nominal_ratio={}, cur={}, dev={}, threshold={}".format(
                    nominal_ratio, cur, dev, threshold
                )
            else:
                ratios = ratios[-nanalyses:]
                self._ratios[atype] = ratios

                n = len(ratios)
                self.debug("n={}, RunIDs={}".format(n, ",".join([ri[1] for ri in ratios])))
                if n == nanalyses:
                    xs = [nominal_value(ri[2]) for ri in ratios[:-1]]
                    es = [std_dev(ri[2]) for ri in ratios[:-1]]
                    wm, werr = calculate_weighted_mean(xs, es)
                    mswd = calculate_mswd(xs, es, wm=wm)
                    cur = nominal_value(ratios[-1][2])
                    dev = abs(wm - cur)
                    if pthreshold:
                        threshold = pthreshold
                        dev = (dev / wm) * 100

                    if not threshold:
                        threshold = nsigma * werr

                    if mswd_threshold:
                        threshold = mswd_threshold
                        dev = mswd
                    msg = "wm={}+/-{}, mswd={}, cur={}, dev={}, threshold={}".format(
                        wm, werr, mswd, cur, dev, threshold
                    )
                else:
                    return

            self.debug(msg)
            if dev > threshold:
                if not nominal_ratio:
                    excluded.append(ratios[-1][0])
                    self._excluded_uuids[atype] = excluded

                fc = self._failure_counts.get(atype, 0) + 1
                self._failure_counts[atype] = fc
                msg = "Ratio change detected. {}, Total failures={}/{}".format(msg, fc, failure_cnt)
                self.debug(msg)
                if fc >= failure_cnt:
                    if send_email_only:
                        pass
                    else:
                        self._err_message = msg
                        invoke_in_main_thread(self.warning_dialog, msg)
                        return True
            else:
                if consecutive_failure:
                    self._failure_counts[atype] = 0

    def _check_scheduled_stop(self, spec):
        """
        return True if the end time of the upcoming run is greater than the scheduled stop time
        :param spec:
        :return:
        """

        scheduled_stop = self.scheduler.stop_dt
        if scheduled_stop is not None:
            et = self.stats.get_endtime(spec)
            self.debug(
                "Scheduled stop check. Run End Time={}, Scheduled={}".format(et, scheduled_stop)
            )
            return et > scheduled_stop

    def _check_for_email_plugin(self, inform):
        if any((eq.use_email or eq.use_group_email for eq in self.experiment_queues)):
            if not self.application.get_plugin("pychron.social.email.plugin"):
                if inform:
                    return self.confirmation_dialog(
                        "Email Plugin not initialized. "
                        "Required for sending email notifications. "
                        "Are you sure you want to continue?"
                    )
                else:
                    return False

        return True

    def _check_dashboard(self, inform):
        """
        return True if dashboard has an error
        :return: boolean
        """
        if self.use_dashboard_client:
            if self.dashboard_client:
                ef = self.dashboard_client.error_flag
                if ef:
                    self._err_message = "Dashboard error. {}".format(ef)
                    self.warning(
                        "Canceling experiment. Dashboard client reports an error\n {}".format(ef)
                    )
                    return

        return True

    def _check_memory(self, inform, threshold=None):
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
            self.debug("Available memory {}. mem-threshold= {}".format(amem, threshold))
            if amem < threshold:
                msg = "Memory limit exceeded. Only {} MB available. Stopping Experiment".format(
                    amem
                )
                if inform:
                    invoke_in_main_thread(self.warning_dialog, msg)
                return

        return True

    def _check_managers(self, inform=True):
        self.debug("checking for managers")
        if globalv.experiment_debug:
            self.debug("********************** NOT DOING  managers check")
            return True

        nonfound = self._check_for_managers()
        if nonfound:
            self.info("experiment canceled because could connect to managers {}".format(nonfound))
            self._err_message = 'Could not connect to "{}"'.format(",".join(nonfound))

            return

        return True

    def _check_for_managers(self):
        """
        determine the necessary managers based on the ExperimentQueue and
        check that they exist and are connectable
        """
        from pychron.experiment.connectable import Connectable

        exp = self.experiment_queue
        nonfound = []
        elm_connectable = Connectable(name="Extraction Line", manager=self.extraction_line_manager)
        self.connectables = [elm_connectable]

        if self.extraction_line_manager is None:
            nonfound.append("extraction_line")
        else:
            if not self.extraction_line_manager.test_connection():
                nonfound.append("extraction_line")
            else:
                elm_connectable.connected = True

        if exp.extract_device and exp.extract_device not in NULL_EXTRACT_DEVICES:
            # extract_device = convert_extract_device(exp.extract_device)
            extract_device = exp.extract_device.replace(" ", "")
            ed_connectable = Connectable(name=extract_device)
            man = None
            if self.application:
                self.debug("get service name={}".format(extract_device))
                for protocol in (
                    ILASER_PROTOCOL,
                    IFURNACE_PROTOCOL,
                    IPIPETTE_PROTOCOL,
                    CRYO_PROTOCOL,
                ):
                    man = self.application.get_service(
                        protocol, 'name=="{}"'.format(extract_device)
                    )
                    if man:
                        ed_connectable.protocol = protocol
                        break

            self.connectables.append(ed_connectable)
            if not man:
                nonfound.append(extract_device)
            else:
                connected, error = man.test_connection()
                if not connected:
                    nonfound.append(extract_device)
                else:
                    ed_connectable.set_connection_parameters(man)
                    ed_connectable.connected = True

        needs_spec_man = any(
            [ai.measurement_script for ai in exp.cleaned_automated_runs if ai.state == "not run"]
        )

        if needs_spec_man:
            s_connectable = Connectable(name="Spectrometer", manager=self.spectrometer_manager)
            self.connectables.append(s_connectable)
            if self.spectrometer_manager is None:
                nonfound.append("spectrometer")
            else:
                if not self.spectrometer_manager.test_connection():
                    nonfound.append("spectrometer")
                else:
                    s_connectable.connected = True

        return nonfound

    def _check_for_massspec_db(self, inform):
        if self.use_db_persistence:
            if self.datahub.massspec_enabled:
                if not self.datahub.store_connect("massspec"):
                    if inform:
                        return self.confirmation_dialog(
                            "Not connected to a Mass Spec database. Do you want to continue with pychron only?"
                        )
                    else:
                        return False

        return True

    def _check_first_aliquot(self, inform):
        exp = self.experiment_queue
        runs = exp.cleaned_automated_runs

        # check the first aliquot before delaying
        arv = runs[0]
        if not self._set_run_aliquot(arv):
            if inform:
                self.warning_dialog("Failed setting aliquot")
            return
        else:
            return True

    def _check_dated_repos(self, inform):
        if self.use_dvc_persistence:
            exp = self.experiment_queue
            runs = exp.cleaned_automated_runs

            # create dated references repos
            curtag = get_curtag()

            dvc = self.datahub.stores["dvc"]
            ms = self.active_editor.queue.mass_spectrometer
            for tag in ("air", "cocktail", "blank"):
                repo = "{}_{}{}".format(ms, tag, curtag)
                dvc.add_repository(repo, self.default_principal_investigator, inform=False)
                dvc.add_readme(repo)

            no_repo = []
            for i, ai in enumerate(runs):
                if not ai.repository_identifier:
                    self.warning("No repository identifier for i={}, {}".format(i + 1, ai.runid))
                    no_repo.append(ai)

            if no_repo:
                if inform:
                    if not self.confirmation_dialog(
                        "Missing repository identifiers. Automatically populate?"
                    ):
                        return

                populate_repository_identifiers(no_repo, ms, curtag, debug=self.debug)

        return True

    def _check_automated_run_monitor(self, inform):
        if self.use_automated_run_monitor:
            self.monitor = self._monitor_factory()
            if self.monitor:
                self.monitor.set_additional_connections(self.connectables)
                self.monitor.clear_errors()
                if not self.monitor.check():
                    return
        return True

    def _check_pyscript_runner(self, inform):
        if not self.pyscript_runner.connect():
            self.info("Failed connecting to pyscript_runner")
            msg = "Failed connecting to a pyscript_runner. Is the extraction line computer running?"
            if inform:
                invoke_in_main_thread(self.warning_dialog, msg)
            return
        return True

    def _check_preceding_blank(self, inform):
        mainstore = self.datahub.mainstore
        with mainstore.session_ctx(use_parent_session=True):
            an = self._get_previous_blank_from_db(inform=inform)
            if an is not True:
                if an is None:
                    return
                else:
                    self.info("using {} as the previous blank".format(an.record_id))
                    try:
                        self._set_prev(an)

                    except TraitError:
                        self.debug_exception()
                        self.warning("failed loading previous blank")
                        return
        return True

    def _check_locked_valves(self, inform):
        elm = self.extraction_line_manager
        locks = elm.get_locked()
        if locks:
            if inform:
                prep, suf = "are", "s"
                if len(locks) == 1:
                    prep, suf = "is", ""
                return self.confirmation_dialog(
                    'Valve{} "{}" {} locked. '
                    "Do you want to continue?".format(suf, ",".join(locks), prep)
                )

        return True

    def _check_no_runs(self, inform):
        exp = self.experiment_queue
        runs = exp.cleaned_automated_runs
        if not len(runs):
            if inform:
                self.warning_dialog("No analysis in the queue")
            return
        return True

    def _pre_execute_check(self, prog=None, inform=True):
        if globalv.experiment_debug:
            self.debug("********************** NOT DOING PRE EXECUTE CHECK ")
            return True

        if (
            not self.use_db_persistence
            and not self.use_xls_persistence
            and not self.use_dvc_persistence
        ):
            if not self.confirmation_dialog(
                "You do not have any Database or XLS saving enabled. "
                "Are you sure you want to continue?\n\n"
                "Enable analysis saving in Preferences>>Experiment>>Automated Run"
            ):
                return

        funcs = (
            (self._check_no_runs, "Check No Runs"),
            (self._check_for_email_plugin, "Check For Email Plugin"),
            (self._check_for_massspec_db, "Check For Mass Spec Plugin"),
            (self._check_first_aliquot, "Setting Aliquot"),
            (
                self._check_dated_repos if self.use_dvc_persistence else None,
                "Setup Dated Repositories",
            ),
            (
                (self._check_repository_identifiers if self.use_dvc_persistence else None),
                "Check Repositories",
            ),
            (self._check_managers, "Check Managers"),
            (self._check_dashboard, "Check  Dashboard"),
            (self._check_memory, "Check Memory"),
            (self._check_automated_run_monitor, "Check Automated Run Monitor"),
            (self._check_pyscript_runner, "Check Pyscript Runner"),
            (self._check_locked_valves, "Locked Valves"),
            (self._check_preceding_blank, "Set Preceding Blank"),
        )

        for func, msg in funcs:
            if not func:
                continue

            self.debug("checking: {}".format(msg))
            if prog:
                prog.change_message(msg)
            if not func(inform):
                raise PreExecuteCheckException(msg, self._err_message)

        # Sync queue metadata (including repository_identifier) to runs before syncing repositories
        for q in self.experiment_queues:
            q.sync_queue_meta(force=True)

        if prog:
            prog.change_message("Syncing repositories")

        e = self._sync_repositories(prog)
        if e:
            raise PreExecuteCheckException('Syncing Repository "{}"'.format(e))

        if prog:
            prog.change_message("Pre execute check complete")

        self.debug("pre execute check complete")
        return True

    def _pre_step_check(self, run, tag):
        """
        do pre_run_terminations

        return True to fail
        """

        if not self.alive:
            return

        self.debug(
            "============================= Pre {} Check =============================".format(tag)
        )

        conditionals = self._load_queue_conditionals("pre_run_terminations")
        default_conditionals = self._load_system_conditionals("pre_run_terminations")
        if default_conditionals or conditionals:
            self.heading("Pre Extraction Check")

            self.debug("Get a measurement from the spectrometer")
            data = self.spectrometer_manager.spectrometer.get_intensities()
            ks = ",".join(data[0])
            ss = ",".join(["{:0.5f}".format(d) for d in data[1]])
            self.debug("Pre Extraction Termination data. keys={}, signals={}".format(ks, ss))

            if conditionals:
                self.info("testing user defined conditionals")
                if self._test_conditionals(
                    run,
                    conditionals,
                    "Checking user defined pre extraction terminations",
                    "Pre Extraction Termination",
                    data=data,
                ):
                    return True

            if default_conditionals:
                self.info("testing system defined conditionals")
                if self._test_conditionals(
                    run,
                    default_conditionals,
                    "Checking default pre extraction terminations",
                    "Pre Extraction Termination",
                    data=data,
                ):
                    return True

            self.heading("Pre Extraction Check Passed")
        self.debug(
            "================================================================================="
        )

    def _pre_queue_check(self, exp):
        """
        return True to stop execution loop
        """
        self.debug("pre queue check: tray={}".format(exp.tray))
        if exp.tray and exp.tray != NULL_STR:
            ed = next((ci for ci in self.connectables if ci.name == exp.extract_device), None)
            if ed and ed.connected:
                name = convert_extract_device(ed.name)
                man = self.application.get_service(ed.protocol, 'name=="{}"'.format(name))
                self.debug('Get service {}. name=="{}"'.format(ed.protocol, name))
                if man:
                    self.debug("{} service found {}".format(name, man))
                    if hasattr(man, "get_tray"):
                        ed_tray = man.get_tray()
                        ret = ed_tray != exp.tray
                        if ret:
                            if hasattr(man, "set_tray"):
                                msg = (
                                    'The laser is configured to use tray: "{}" but the experiment is set to use '
                                    'tray: "{}".\n\n'
                                    'Would you like to set the laser to use "{}"'.format(
                                        ed_tray, exp.tray, exp.tray
                                    )
                                )
                                if self.confirmation_dialog(msg):
                                    man.set_tray(exp.tray)
                                    ret = False
                                else:
                                    if self.confirmation_dialog(
                                        "Laser tray not necessarily setup correctly."
                                        "\n\nAre you sure you want to continue?"
                                    ):
                                        ret = False

                        return ret

    def _pre_run_check(self, spec, inform=False):
        """
        return True to stop execution loop
        """
        self.heading("Pre Run Check")

        if not self._check_dashboard(inform):
            return True

        if not self._check_memory(inform):
            self._err_message = "Not enough memory"
            return True

        if not self._check_managers(inform):
            self._err_message = "Not all managers available"
            return True

        if self._check_for_errors(inform):
            return True

        if self.monitor:
            if not self.monitor.check():
                self._err_message = "Automated Run Monitor Failed"
                self.warning("automated run monitor failed")
            return True

        # if the experiment queue has been modified wait until saved or
        # timed out. if timed out autosave.
        self._wait_for_save()
        self.heading("Pre Run Check Passed")

    # def _retroactive_repository_identifiers(self, spec):
    #     self.warning('retroactive repository identifiers disabled')
    #     return
    #
    #     db = self.datahub.mainstore
    #     crun, expid = retroactive_repository_identifiers(spec, self._cached_runs, self._active_repository_identifier)
    #     self._cached_runs, self._active_repository_identifier = crun, expid
    #
    #     db.add_repository_association(spec.repository_identifier, spec)
    #     if not is_special(spec.identifier) and self._cached_runs:
    #         for c in self._cached_runs:
    #             db.add_repository_association(expid, c)
    #         self._cached_runs = []

    def _check_repository_health(self, inform):
        for ei in self.experiment_queues:
            repos = {ai.repository_identifier for ai in ei.cleaned_automated_runs}
            for ri in repos:
                self.datahub.mainstore

    def _check_repository_identifiers(self, inform):
        db = self.datahub.mainstore.db

        cr = ConflictResolver()
        with db.session_ctx():
            for ei in self.experiment_queues:
                identifiers = {ai.identifier for ai in ei.cleaned_automated_runs}
                identifiers = [idn for idn in identifiers if not is_special(idn)]

                repositories = {}
                eas = db.get_associated_repositories(identifiers)
                for idn, exps in groupby_key(eas, itemgetter(1)):
                    # for idn, exps in groupby(eas, key=lambda x: x[1]):
                    repositories[idn] = [e[0] for e in exps]

                conflicts = []
                for ai in ei.cleaned_automated_runs:
                    identifier = ai.identifier
                    if not is_special(identifier):
                        try:
                            es = repositories[identifier]
                            if ai.repository_identifier not in es:
                                if ai.sample == self.monitor_name:
                                    ai.repository_identifier = "Irradiation-{}".format(
                                        ai.irradiation
                                    )

                                else:
                                    self.debug(
                                        "Repository association conflict. "
                                        "repository={} "
                                        "previous_associations={}".format(
                                            ai.repository_identifier, ",".join(es)
                                        )
                                    )
                                    conflicts.append((ai, es))
                        except KeyError:
                            pass

                if conflicts:
                    self.debug("Repository association warning")
                    cr.add_conflicts(ei.name, conflicts)

            if cr.conflicts:
                cr.available_ids = db.get_repository_identifiers()

                info = cr.edit_traits(kind="livemodal")
                if info.result:
                    cr.apply()
                    self.experiment_queue.refresh_table_needed = True
                    return True
            else:
                return True

    def _sync_repositories(self, prog):
        if self.use_dvc_persistence:
            experiment_ids = {
                a.repository_identifier
                for q in self.experiment_queues
                for a in q.cleaned_automated_runs
            }
            for e in experiment_ids:
                if prog:
                    prog.change_message("Syncing {}".format(e))
                try:
                    if not self.datahub.mainstore.sync_repo(e, use_progress=False):
                        self.warning(f"Failed to sync repository '{e}': sync_repo returned False")
                        return f"{e} (sync failed)"
                    if not self.datahub.mainstore.is_clean(e):
                        # Try to auto-recover clean state
                        if prog:
                            prog.change_message("Cleaning repository state {}".format(e))
                        from pychron.dvc.repository_sync import _recover_clean_state
                        if not _recover_clean_state(self.datahub.mainstore, e):
                            self.warning(f"Repository '{e}' is not clean (has uncommitted changes or diverged history)")
                            return f"{e} (not clean)"
                except Exception as ex:
                    self.warning(f"Exception syncing repository '{e}': {ex}")
                    return f"{e} (error: {str(ex)})"

    def _post_run_check(self, run):
        """
        1. check post run termination conditionals.
        2. check to see if an action should be taken

        if runs  are overlapping this will be a problem.
        dont overlap onto blanks
        execute the action and continue the queue
        """
        if not self.alive:
            return
        self.heading("Post Run Check")

        if self._ratio_change_detection(run.spec):
            self.warning("Ratio Change Detected")
            return True

        # check user defined post run actions
        # conditionals = self._load_queue_conditionals('post_run_actions', klass='ActionConditional')
        conditionals = self._load_queue_conditionals("post_run_actions")
        if self._action_conditionals(
            run,
            conditionals,
            "Checking user defined post run actions",
            "Post Run Action",
        ):
            return True

        # check default post run actions
        # conditionals = self._load_default_conditionals('post_run_actions', klass='ActionConditional')
        conditionals = self._load_system_conditionals("post_run_actions")
        if self._action_conditionals(
            run, conditionals, "Checking default post run actions", "Post Run Action"
        ):
            return True

        # check queue defined terminations
        conditionals = self._load_queue_conditionals("post_run_terminations")
        if self._test_conditionals(
            run,
            conditionals,
            "Checking user defined post run terminations",
            "Post Run Termination",
            cgroup="terminations",
        ):
            return True

        # check default terminations
        conditionals = self._load_system_conditionals("post_run_terminations")
        if self._test_conditionals(
            run,
            conditionals,
            "Checking default post run terminations",
            "Post Run Termination",
            cgroup="terminations",
        ):
            return True

    def _check_for_errors(self, inform):
        self.debug("checking for connectable errors")
        ret = False
        for c in self.connectables:
            self.debug("check connectable name: {} manager: {}".format(c.name, c.manager))
            man = c.manager
            if man is None:
                man = self.application.get_service(c.protocol, 'name=="{}"'.format(c.name))

            self.debug("connectable manager: {}".format(man))
            if man:
                e = man.get_error()
                self.debug("connectable get error {}".format(e))
                if e and e.lower() != "ok":
                    self._err_message = e
                    ret = True
                    break

        return ret

    def _load_system_conditionals(self, term_name, **kw):
        self.debug("loading system conditionals {}".format(term_name))
        # p = paths.system_conditionals
        p = get_path(paths.spectrometer_dir, ".*conditionals", [".yaml", ".yml"])
        if p:
            return self._extract_conditionals(p, term_name, level=SYSTEM, **kw)
        else:
            # pp = os.path.join(paths.spectrometer_dir, 'default_conditionals.yaml')
            self.warning(
                'no system conditionals file located at "{}"'.format(paths.spectrometer_dir)
            )

    def _load_queue_conditionals(self, term_name, **kw):
        self.debug("loading queue conditionals {}".format(term_name))
        exp = self.experiment_queue
        if not exp and self.active_editor:
            exp = self.active_editor.queue

        if exp:
            name = exp.queue_conditionals_name
            if test_queue_conditionals_name(name):
                p = get_path(paths.queue_conditionals_dir, name, [".yaml", ".yml"])
                self.debug("queue conditionals path {}".format(p))
                return self._extract_conditionals(p, term_name, level=QUEUE, **kw)

    def _extract_conditionals(self, p, term_name, level=RUN, **kw):
        if p and os.path.isfile(p):
            self.debug("loading conditionals from {}".format(p))
            return conditionals_from_file(p, name=term_name, level=level, **kw)

    def _action_conditionals(self, run, conditionals, message1, message2):
        if conditionals:
            self.debug("{} n={}".format(message1, len(conditionals)))
            for ci in conditionals:
                if ci.check(run, None, True):
                    self.info("{}. {}".format(message2, ci.to_string()), color="yellow")
                    self._show_conditionals(active_run=run, tripped=ci, kind="live")
                    self._do_action(ci)

                    if self._cv_info:
                        invoke_in_main_thread(do_after, 2000, self._close_cv)

                    return True

    def _test_conditionals(
        self, run, conditionals, message1, message2, cgroup=None, data=None, cnt=True
    ):
        if not self.alive:
            return True

        if conditionals:
            self.debug("{} n={}".format(message1, len(conditionals)))
            for ci in conditionals:
                if ci.check(run, data, cnt):
                    self.warning("!!!!!!!!!! Conditional Tripped !!!!!!!!!!")
                    self.warning("{}. {}".format(message2, ci.to_string()))

                    self.cancel(confirm=False)
                    kw = {}
                    if cgroup:
                        kw["conditionals"] = {cgroup: conditionals}

                    self.show_conditionals(active_run=run, tripped=ci, **kw)
                    return True

    def _do_action(self, action):
        self.info("Do queue action {}".format(action.action))
        if action.action == "repeat":
            if action.count < action.nrepeat:
                self.debug("repeating last run")
                action.count += 1
                exp = self.experiment_queue

                run = exp.executed_runs[0]
                exp.automated_runs.insert(0, run)

                # experimentor handles the queue modified
                # resets the database and updates info
                self.queue_modified = True

            else:
                self.info("executed N {} {}s".format(action.count + 1, action.action))
                self.cancel(confirm=False)

        elif action.action == "cancel":
            self.cancel(confirm=False)

    def _get_previous_blank_from_db(self, inform=True):
        if not self.use_preceding_blank:
            return True

        exp = self.experiment_queue

        types = ["air", "unknown", "cocktail"]
        # get first air, unknown or cocktail
        aruns = exp.cleaned_automated_runs

        if aruns[0].analysis_type.startswith("blank"):
            return True

        msg = """First "{}" not preceded by a blank.
Use Last "blank_{}"= {}
"""
        an = next((a for a in aruns if a.analysis_type in types), None)
        if an:
            anidx = aruns.index(an)

            # find first blank_
            # if idx > than an idx need a blank
            nopreceding = True
            ban = next(
                (a for a in aruns if a.analysis_type == "blank_{}".format(an.analysis_type)),
                None,
            )

            if ban:
                nopreceding = aruns.index(ban) > anidx

            if nopreceding:
                self.debug("no preceding blank")
            if anidx == 0:
                self.debug("first analysis is not a blank")

            if anidx == 0 or nopreceding:
                pdbr, selected = self._get_blank(
                    an.analysis_type,
                    exp.mass_spectrometer,
                    exp.extract_device,
                    last=True,
                )

                if pdbr:
                    if selected:
                        self.debug("use user selected blank {}".format(pdbr.record_id))
                        return pdbr
                    else:
                        retval = NO
                        if inform:
                            retval = self.confirmation_dialog(
                                msg.format(an.analysis_type, an.analysis_type, pdbr.record_id),
                                no_label="Select From Database",
                                cancel=True,
                                return_retval=True,
                            )

                        if retval == CANCEL:
                            return
                        elif retval == YES:
                            self.debug("use default blank {}".format(pdbr.record_id))
                            return pdbr
                        else:
                            self.debug("get blank from database")
                            pdbr, _ = self._get_blank(
                                an.analysis_type,
                                exp.mass_spectrometer,
                                exp.extract_device,
                            )
                            return pdbr
                else:
                    self.warning_dialog(
                        "No blank for {} is in the database. Run a blank!!".format(an.analysis_type)
                    )
                    return

        return True

    def _get_blank(self, kind, ms, ed, last=False, repository=None):
        mainstore = self.datahub.mainstore

        db = mainstore.db
        selected = False
        dbr = None
        if last:
            dbr = db.retrieve_blank(kind, ms, ed, last, repository)

        if dbr is None:
            selected = True
            from pychron.experiment.utilities.reference_analysis_selector import (
                ReferenceAnalysisSelector,
            )

            selector = ReferenceAnalysisSelector(title="Select a Blank")
            info = selector.edit_traits(kind="livemodal")
            dbs = db.get_blanks(ms)
            selector.init("Select Default Blank", dbs)
            if info.result:
                dbr = selector.selected
        if dbr:
            dbr = mainstore.make_analysis(dbr)

        return dbr, selected

    def _set_message(self, msg, color="black"):
        self.heading(msg)
        self.experiment_status.set_state(msg, False, color)
        # invoke_in_main_thread(self.trait_set, extraction_state_label=msg,
        #                       extraction_state_color=color)

    _low_post = None

    def _update_timeseries(self, low_post=None):
        if self.use_dvc_persistence:
            if low_post is None:
                low_post = self._low_post
            else:
                self._low_post = low_post

            dvc = self.datahub.mainstore
            # with dvc.session_ctx(use_parent_session=True):
            if self.experiment_queue:
                ms = self.experiment_queue.mass_spectrometer
            else:
                if not self.timeseries_mass_spectrometers:
                    self.timeseries_mass_spectrometers = dvc.get_mass_spectrometer_names()

                info = self.edit_traits(
                    view=okcancel_view(
                        UItem(
                            "timeseries_mass_spectrometer",
                            # label='Mass Spectrometer',
                            editor=EnumEditor(name="timeseries_mass_spectrometers"),
                        ),
                        title="Please Select a Mass Spectrometer",
                        width=300,
                    ),
                    kind="livemodal",
                )
                if info.result:
                    ms = self.timeseries_mass_spectrometer
                else:
                    return

            with dvc.db.session_ctx():
                ans = dvc.db.get_last_n_analyses(
                    self.timeseries_n_recall,
                    mass_spectrometer=ms,
                    exclude_types=("unknown",),
                    low_post=low_post,
                    verbose=True,
                    # use_parent_session=True,
                )
                ans = dvc.make_analyses(ans, use_progress=False)
                if ans:
                    self.timeseries_editor.set_items(ans)
                    invoke_in_main_thread(self.timeseries_editor.refresh)
                else:
                    self.warning("failed retrieving analyses for experiment timeseries")

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _timeseries_refresh_button_fired(self):
        self._update_timeseries()

    def _timeseries_reset_button_fired(self):
        self._low_post = datetime.now()
        self.information_dialog(
            "Timeseries reset to {}".format(self._low_post.strftime("%m/%d/%y %H:%M"))
        )
        self._update_timeseries()

    # def _configure_timeseries_editor_button_fired(self):
    #
    #     info = OptionsController(model=self.timeseries_options).edit_traits(
    #         view=view("Timeseries Options"), kind="livemodal"
    #     )
    #     if info.result:
    #         self.timeseries_editor.set_options(self.timeseries_options.selected_options)
    #         self.timeseries_editor.refresh()

    def _measuring_run_changed(self):
        if self.measuring_run:
            self.measuring_run.is_last = self.end_at_run_completion

    def _extracting_run_changed(self):
        if self.extracting_run:
            self.extracting_run.is_last = self.end_at_run_completion

    def _end_at_run_completion_changed(self):
        if self.end_at_run_completion:
            if self.measuring_run:
                self.measuring_run.is_last = True
            if self.extracting_run:
                self.extracting_run.is_last = True
        else:
            self._update_automated_runs()

    @on_trait_change("experiment_queue:automated_runs[]")
    def _update_automated_runs(self):
        if self.is_alive():
            is_last = len(self.experiment_queue.cleaned_automated_runs) == 0
            if self.extracting_run:
                self.extracting_run.is_last = is_last

    @on_trait_change("experiment_queue:selected, active_editor:queue:selected")
    def _handle_selection(self, new):
        if new:
            self.selected_run = new[0]
        else:
            self.selected_run = None

    def _handle_executor_event(self, obj, name, new):
        kind = new.pop("kind")
        if kind in ("info", "heading"):
            message = new.pop("message")
            if kind == "info":
                func = self.info
            elif kind == "heading":
                func = self.heading

            func(message, **new)
        else:
            if kind == "wait":
                self.wait(new["duration"], new["message"])
            elif kind == "ms_pumptime_start":
                self.ms_pumptime_start = new["time"]
            elif kind == "cancel":
                self.cancel(**new)
            # elif kind == 'previous_baselines':
            #     self._prev_baselines = new['baselines']
            # elif kind == 'previous_blanks':
            #     self._prev_baselines = new['baselines']
            elif kind == "show_conditionals":
                self.show_conditionals(active_run=obj, **new)
            elif kind == "end_after":
                self.end_at_run_completion = True

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_can_start(self):
        return self.executable and not self.is_alive()

    # ===============================================================================
    # defaults
    # ===============================================================================
    # def _timeseries_options_default(self):
    #     opt = SeriesOptionsManager()
    #     opt.set_names_via_keys(ARGON_KEYS)
    #     return opt

    def _timeseries_editor_default(self):
        ed = AnalysisGroupedSeriesEditor()
        ed.init(atypes=["air", "cocktail", "blank_unknown", "blank_air", "blank_cocktail"])
        # ed.set_options(self.timeseries_options.selected_options)

        return ed

    def _dashboard_client_default(self):
        if self.use_dashboard_client:
            return self.application.get_service("pychron.dashboard.client.DashboardClient")

    def _scheduler_default(self):
        return ExperimentScheduler()

    def _datahub_default(self):
        dh = Datahub()
        dh.mainstore = self.application.get_service(DVC_PROTOCOL)
        dh.bind_preferences()
        return dh

    def _pyscript_runner_default(self):
        runner = self.application.get_service(
            "pychron.extraction_line.ipyscript_runner.IPyScriptRunner"
        )
        return runner

    def _monitor_factory(self):
        self.debug("Experiment Executor mode={}".format(self.mode))
        if self.mode == "client":
            from pychron.monitors.automated_run_monitor import RemoteAutomatedRunMonitor

            mon = RemoteAutomatedRunMonitor(name="automated_run_monitor")
        else:
            from pychron.monitors.automated_run_monitor import AutomatedRunMonitor

            mon = AutomatedRunMonitor()

        mon.extraction_line_manager = self.extraction_line_manager
        self.debug("Automated run monitor {}".format(mon))
        if mon is not None:
            isok = mon.load()
            if isok:
                return mon
            else:
                self.warning(
                    "no automated run monitor available. "
                    "Make sure config file is located at setupfiles/monitors/automated_run_monitor.cfg"
                )


# ============= EOF =============================================
