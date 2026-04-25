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
import os
import shutil
import time
from typing import Optional

import xlrd
from pyface.constant import CANCEL, NO
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter, Tabbed
from pyface.timer.do_later import do_after
from traits.api import on_trait_change, Bool, Instance, Event

from pychron.core.helpers.filetools import add_extension, backup
from pychron.core.helpers.strtools import to_bool
from pychron.envisage.tasks.editor_task import EditorTask
from pychron.envisage.tasks.pane_helpers import ConsolePane
from pychron.envisage.tasks.wait_pane import WaitPane
from pychron.envisage.view_util import open_view
from pychron.experiment.experiment_launch_history import update_launch_history
from pychron.experiment.experimentor import Experimentor
from pychron.experiment.queue.base_queue import extract_meta
from pychron.experiment.tasks.experiment_editor import (
    ExperimentEditor,
    UVExperimentEditor,
)
from pychron.experiment.tasks.experiment_panes import (
    ExperimentFactoryPane,
    StatsPane,
    ControlsPane,
    IsotopeEvolutionPane,
    ConnectionStatusPane,
    LoggerPane,
    ExplanationPane,
    ConditionalsPane,
    TimeSeriesPane,
)
from pychron.extraction_line.tasks.extraction_line_actions import (
    ToggleAutomatedValveConfirmationAction,
)
from pychron.experiment.utilities.identifier import convert_extract_device, is_special
from pychron.experiment.utilities.save_dialog import ExperimentSaveDialog
from pychron.globals import globalv
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.paths import paths
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pychron_constants import (
    SPECTROMETER_PROTOCOL,
    DVC_PROTOCOL,
    COCKTAIL,
    AIR,
    BLANK,
    FUSIONS_UV,
    INVALID,
    EXTRACTION,
    MEASUREMENT,
    CANCELED,
    TRUNCATED,
    END_AFTER,
    FAILED,
    SUCCESS,
)


class ExperimentEditorTask(EditorTask):
    id = "pychron.experiment.task"
    name = "Experiment"

    default_open_action = "open files"
    wildcard = "*.txt"

    loading_manager = Instance("pychron.loading.loading_manager.LoadingManager")

    last_experiment_changed = Event

    # bgcolor = Color
    # even_bgcolor = Color
    # use_analysis_type_color = Bool

    automated_runs_editable = Bool

    conditionals_pane = Instance(ConditionalsPane)
    isotope_evolution_pane = Instance(IsotopeEvolutionPane)
    experiment_factory_pane = Instance(ExperimentFactoryPane)

    load_pane = Instance("pychron.loading.tasks.panes.LoadDockPane")
    load_table_pane = Instance("pychron.loading.tasks.panes.LoadTablePane")
    laser_control_client_pane = None

    events = None
    dock_pane_factories = None
    activations = None
    deactivations = None
    _layout_reset = False
    _adjust_extraction_canvas_split_timer = None
    _update_info_timer = None

    def save_as_current_experiment(self):
        self.debug("save as current experiment")
        if self.has_active_editor():
            path = os.path.join(paths.experiment_dir, "CurrentExperiment.txt")
            self.save(path=path)

    def configure_experiment_table(self):
        if self.has_active_editor():
            self.active_editor.show_table_configurer()

    def new_pattern(self):
        pm = self._pattern_maker_view_factory()
        open_view(pm)

    def open_pattern(self):
        pm = self._pattern_maker_view_factory()
        if pm.load_pattern():
            open_view(pm)

    def deselect(self):
        if self.active_editor:
            self.active_editor.queue.selected = []
            self.active_editor.queue.executed_selected = []

    def undo(self):
        if self.has_active_editor():
            self.manager.experiment_factory.undo()

    def edit_queue_conditionals(self):
        if self.has_active_editor():
            from pychron.experiment.conditional.conditionals_edit_view import (
                edit_conditionals,
            )

            dnames = None
            spec = self.application.get_service(
                "pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager"
            )
            if spec:
                dnames = spec.spectrometer.detector_names

            edit_conditionals(
                self.manager.experiment_factory.queue_factory.queue_conditionals_name,
                detectors=dnames,
            )

    def reset_queues(self):
        for editor in self.editor_area.editors:
            editor.queue.reset()

        man = self.manager
        ex = man.executor
        ex.stats.reset()

        man.update_info()

        ex.end_at_run_completion = False
        ex.set_extract_state("")

    def sync_queue(self):
        """
        sync queue to database
        """
        if not self.has_active_editor():
            return
        queue = self.active_editor.queue
        self.manager.sync_queue(queue)

    def new(self):
        """
        open a blank experiment editor
        :return:
        """
        manager = self.manager
        if manager.verify_database_connection(inform=True):
            if manager.load():
                self.manager.experiment_factory.activate(load_persistence=True)

                editor = self._editor_factory()
                editor.new_queue()

                self._open_editor(editor)
                if self.loading_manager:
                    self.loading_manager.clear()
                    self.manager.experiment_factory.loading_manager = self.loading_manager

                if not self.manager.executor.is_alive():
                    self.manager.executor.executable = False
                return True

    def bind_preferences(self):
        # notifications

        self._preference_binder("pychron.experiment", ("automated_runs_editable",))

        # color_bind_preference(self, 'bgcolor', 'pychron.experiment.bg_color')
        # color_bind_preference(self, 'even_bgcolor', 'pychron.experiment.even_bg_color')

    # ===============================================================================
    # tasks protocol
    # ===============================================================================
    def activated(self):
        self.bind_preferences()
        super(ExperimentEditorTask, self).activated()
        self.debug(
            "experiment_task activated window_present={} layout_reset={} editors={} active_editor={} ".format(
                self.window is not None,
                self._layout_reset,
                len(self.editor_area.editors) if self.editor_area else 0,
                type(self.active_editor).__name__ if self.active_editor is not None else None,
            )
        )

        if not self._layout_reset and self.window is not None:
            self.window.reset_layout()
            self.debug("Extraction canvas split adjustment scheduled in 500ms")
            
            # Try to restore saved layout state first, otherwise fix the extraction canvas split.
            if not self._restore_window_layout():
                self._schedule_extraction_canvas_split(500)
            
            self._layout_reset = True

        self._do_callables(self.activations)
    
    def _restore_window_layout(self):
        """Restore a previously saved window layout state from preferences.
        
        Returns True if layout was restored, False otherwise.
        """
        try:
            prefs = self.application.preferences
            state_str = prefs.get('pychron.experiment.window_layout_state')
            
            if state_str:
                # Parse the layout state string and restore it
                layout_state = eval(state_str)
                self.window.set_layout_state(layout_state)
                self.debug("Window layout state restored from preferences")
                return True
        except Exception as e:
            self.debug(f"Failed to restore window layout: {e}")
            import traceback
            self.debug(traceback.format_exc())
        
        return False
    
    def _find_host_splitter(self, control) -> tuple[Optional[object], int]:
        from pyface.qt.QtWidgets import QSplitter

        widget = control
        while widget is not None:
            parent = widget.parent()
            if isinstance(parent, QSplitter):
                idx = parent.indexOf(widget)
                if idx != -1:
                    return parent, idx
            widget = parent

        return None, -1

    def _adjust_extraction_canvas_split(self) -> None:
        """Restore the extraction canvas pane size after Qt rebuilds the dock layout.

        Inference: after ``window.reset_layout()``, the Qt splitter does not reliably
        preserve the ``PaneItem(height=...)`` hints from ``TaskLayout``, so the
        extraction-line canvas dock can reopen collapsed.
        """
        self.debug("_adjust_extraction_canvas_split: Starting adjustment")
        try:
            pane = getattr(self, "canvas_pane", None)
            if pane is None:
                self.debug("_adjust_extraction_canvas_split: canvas_pane is None")
                return

            control = getattr(pane, "control", None)
            if control is None:
                self.debug("_adjust_extraction_canvas_split: canvas pane has no control")
                return

            splitter, idx = self._find_host_splitter(control)
            if splitter is None or idx < 0:
                self.debug("_adjust_extraction_canvas_split: no host splitter found")
                return

            count = splitter.count()
            if count < 2:
                self.debug(
                    "_adjust_extraction_canvas_split: splitter child count too small"
                )
                return

            sizes = splitter.sizes()
            total = max(sum(sizes), splitter.height(), count)
            canvas_size = int(total * 0.7)
            other_size = max(1, total - canvas_size)

            if count == 2:
                new_sizes = (
                    [canvas_size, other_size]
                    if idx == 0
                    else [other_size, canvas_size]
                )
            else:
                new_sizes = [1] * count
                new_sizes[idx] = canvas_size
                remaining = max(1, total - canvas_size)
                for i in range(count):
                    if i != idx:
                        new_sizes[i] = max(1, int(remaining / max(1, count - 1)))

            self.debug(
                "_adjust_extraction_canvas_split: setting splitter sizes to {}".format(
                    new_sizes
                )
            )
            splitter.setSizes(new_sizes)
        except Exception as e:
            self.debug(f"_adjust_extraction_canvas_split failed: {e}")
            import traceback
            self.debug(traceback.format_exc())

    def prepare_destroy(self):
        # Save the current window layout state before destroying
        self._save_window_layout()
        self._cancel_delayed_ui_work()
        
        super(ExperimentEditorTask, self).prepare_destroy()

        self.manager.experiment_factory.destroy()
        # self.manager.executor.notification_manager.parent = None

        self._do_callables(self.deactivations)

    def _cancel_timer(self, attr: str) -> None:
        timer = getattr(self, attr, None)
        if timer is None:
            return

        for method_name in ("cancel", "stop"):
            method = getattr(timer, method_name, None)
            if method is None:
                continue
            try:
                method()
            except BaseException as e:
                self.debug(
                    "failed canceling delayed ui work {} using {}: {}".format(
                        attr, method_name, e
                    )
                )
            break

        setattr(self, attr, None)

    def _cancel_delayed_ui_work(self) -> None:
        self._cancel_timer("_adjust_extraction_canvas_split_timer")
        self._cancel_timer("_update_info_timer")

    def _schedule_extraction_canvas_split(self, delay: int) -> None:
        self._cancel_timer("_adjust_extraction_canvas_split_timer")
        self._adjust_extraction_canvas_split_timer = do_after(
            delay, self._adjust_extraction_canvas_split
        )

    def _schedule_update_info(self, delay: int, manager) -> None:
        self._cancel_timer("_update_info_timer")
        self._update_info_timer = do_after(delay, manager.update_info)
    
    def _save_window_layout(self):
        """Save the current window layout state to preferences."""
        if not self.window:
            return
        
        try:
            # Get the current layout state from the window
            layout_state = self.window.get_layout_state()
            if layout_state:
                # Persist to preferences
                prefs = self.application.preferences
                state_str = repr(layout_state)
                prefs.set('pychron.experiment.window_layout_state', state_str)
                self.debug(f"Window layout state saved")
        except Exception as e:
            self.debug(f"Failed to save window layout: {e}")

    def create_dock_panes(self):
        name = "Isotope Evolutions"
        man = self.application.get_service(SPECTROMETER_PROTOCOL)
        if not man or man.simulation:
            name = "{}(Simulation)".format(name)

        ex = self.manager.executor
        self.isotope_evolution_pane = IsotopeEvolutionPane(name=name)

        self.experiment_factory_pane = ExperimentFactoryPane(model=self.manager.experiment_factory)
        wait_pane = WaitPane(model=self.manager.executor.wait_group)

        explanation_pane = ExplanationPane()
        explanation_pane.set_colors(self._assemble_state_colors())
        self.conditionals_pane = ConditionalsPane(model=ex)
        timeseries_pane = TimeSeriesPane(model=ex)

        panes = [
            StatsPane(model=ex.stats, executor=ex),
            ControlsPane(model=ex, task=self),
            ConsolePane(model=ex),
            LoggerPane(),
            ConnectionStatusPane(model=ex),
            self.conditionals_pane,
            self.experiment_factory_pane,
            self.isotope_evolution_pane,
            explanation_pane,
            wait_pane,
            timeseries_pane,
        ]

        if self.loading_manager:
            self.load_pane = self.window.application.get_service(
                "pychron.loading.tasks.panes.LoadDockPane"
            )
            self.load_table_pane = self.window.application.get_service(
                "pychron.loading.tasks.panes.LoadTablePane"
            )

            self.load_pane.model = self.loading_manager
            self.load_table_pane.model = self.loading_manager

            panes.extend([self.load_pane, self.load_table_pane])

        panes = self._add_canvas_pane(panes)
        for p in self.dock_pane_factories:
            pane = p()
            panes.append(pane)

        return panes

    # private
    def _editor_factory(self, is_uv=False, **kw):
        klass = UVExperimentEditor if is_uv else ExperimentEditor
        editor = klass(
            application=self.application, automated_runs_editable=self.automated_runs_editable, **kw
        )

        prefs = self.application.preferences
        prefid = "pychron.experiment"
        bgcolor = prefs.get("{}.bg_color".format(prefid))
        even_bgcolor = prefs.get("{}.even_bg_color".format(prefid))
        use_analysis_type_colors = to_bool(prefs.get("{}.use_analysis_type_colors".format(prefid)))

        editor.setup_tabular_adapters(
            bgcolor,
            even_bgcolor,
            self._assemble_state_colors(),
            use_analysis_type_colors,
            self._assemble_analysis_type_colors(),
        )
        return editor

    def _assemble_analysis_type_colors(self):
        colors = {}
        for c in (BLANK, AIR, COCKTAIL):
            v = self.application.preferences.get("pychron.experiment.{}_color".format(c))
            colors[c] = v or "#FFFFFF"

        return colors

    def _assemble_state_colors(self):
        colors = {}
        for c in (
            SUCCESS,
            EXTRACTION,
            MEASUREMENT,
            CANCELED,
            TRUNCATED,
            FAILED,
            END_AFTER,
            INVALID,
        ):
            v = self.application.preferences.get("pychron.experiment.{}_color".format(c))
            colors[c] = v or "#FFFFFF"

        return colors

    def _do_callables(self, fs):
        for fi in fs:
            if hasattr(fi, "__call__"):
                try:
                    fi()
                except BaseException as e:
                    import traceback

                    traceback.print_exc()
                    self.debug("Callable {} failed. exception={}".format(fi.__name__, str(e)))
            else:
                self.debug("{} not callable".format(fi))

    def _open_file(self, path, **kw):
        if not isinstance(path, (tuple, list)):
            path = (path,)

        manager = self.manager
        # print 'asdfa', manager
        if manager.verify_database_connection(inform=True):
            if manager.load():
                manager.experiment_factory.activate(load_persistence=False)
                for p in path:
                    self.manager.info("Opening experiment {}".format(p))
                    self._open_experiment(p)

                manager.path = path
                # manager.update_info()
                self._schedule_update_info(1000, manager)
                return True

    def _open_experiment(self, path):
        name = os.path.basename(path)
        self.info(
            "------------------------------ Open Experiment {} -------------------------------".format(
                name
            )
        )

        reopen_editor = False
        if name.endswith(".rem.txt") or name.endswith(".ex.txt"):
            ps = name.split(".")
            nname = "{}.txt".format(".".join(ps[:-2]))
            msg = "Rename {} as {}".format(name, nname)
            if self.confirmation_dialog(msg):
                reopen_editor = True
                npath = os.path.join(paths.experiment_dir, nname)

                shutil.copy(path, npath)
                path = npath

        editor = self._check_opened(path)
        if reopen_editor and editor:
            self.close_editor(editor)
            editor = None

        if not editor:
            if path.endswith(".xls"):
                txt, is_uv = self._open_xls(path)
            else:
                txt, is_uv = self._open_txt(path)

            editor = self._editor_factory(is_uv=is_uv, path=path)

            editor.new_queue(txt)
            self._open_editor(editor)
        else:
            self.debug("{} already open. using existing editor".format(name))
            editor.application = self.application
            self.activate_editor(editor)

        # loading queue editor set dirty
        # clear dirty flag
        editor.dirty = False
        self._show_pane(self.experiment_factory_pane)

    def _open_xls(self, path):
        """
        open the workbook and convert it to text
        construct the text to mimic a normal experiment file
        """
        wb = xlrd.open_workbook(path)
        sh = wb.sheet_by_index(0)
        # write meta
        meta_rows = 7
        rows = []
        is_uv = False
        for r in range(meta_rows):
            attr = sh.cell_value(r, 0)
            v = sh.cell_value(r, 1)
            if attr == "extract_device":
                is_uv = v == FUSIONS_UV

            rows.append("{}: {}".format(attr, v))
        rows.append("#{}".format("=" * 80))

        header = sh.row_values(meta_rows)
        rows.append("\t".join(header))
        for r in range(meta_rows + 2, sh.nrows):
            t = "\t".join(map(str, sh.row_values(r)))
            rows.append(t)

        txt = "\n".join(map(str, rows))
        return txt, is_uv

    def _open_txt(self, path):
        with open(path, "r") as rfile:
            txt = rfile.read()

            f = (l for l in txt.split("\n"))
            meta, metastr = extract_meta(f)
            is_uv = False
            if "extract_device" in meta:
                is_uv = meta["extract_device"] in (FUSIONS_UV,)

        return txt, is_uv

    def _check_opened(self, path):
        return next((e for e in self.editor_area.editors if e.path == path), None)

    def _set_last_experiment(self, p):
        with open(paths.last_experiment, "w") as wfile:
            wfile.write(p)
        self.last_experiment_changed = True

        update_launch_history(p)

    def _save_file(self, path):
        if self.active_editor.save(path):
            self.manager.refresh_executable()
            self.debug("queue saved")
            self.manager.reset_run_generator()
            return True

    def _get_save_path(self, default_filename=None, **kw):
        sd = ExperimentSaveDialog(root=paths.experiment_dir, name=default_filename or "Untitled")
        info = sd.edit_traits()
        if info.result:
            return sd.path

    def _generate_default_filename(self):
        name = self.active_editor.queue.load_name
        if name:
            if name.startswith("Load"):
                name = name[4:].strip()

            name = name.replace(" ", "_")

            return "Load{}".format(name)

    def _prompt_for_save(self):
        """
        Prompt the user to save when exiting.
        """
        if self.manager.executor.is_alive():
            name = self.manager.executor.experiment_queue.name
            result = self._confirmation(
                "{} is running. Are you sure you want to quit?".format(name)
            )
            if result in (CANCEL, NO):
                return False
            else:
                ret = super(ExperimentEditorTask, self)._prompt_for_save()
                if ret:
                    self.manager.executor.cancel(confirm=False)
                return ret
        else:
            return super(ExperimentEditorTask, self)._prompt_for_save()

    def _backup_editor(self, editor):
        p = editor.path
        p = add_extension(p, ".txt")

        if os.path.isfile(p):
            # make a backup copy of the original experiment file
            bp, pp = backup(p, paths.backup_experiment_dir)
            self.info("{} - saving a backup copy to {}".format(bp, pp))

    def _close_external_windows(self):
        """
        ask user if ok to close open spectrometer and extraction line windows
        """
        if not self.window:
            return

        # ask user if ok to close windows
        windows = []
        names = []
        # print self.window, self.application
        self.debug("{} calling close_external_windows".format(id(self)))
        if self.application:
            for wi in self.application.windows:
                wid = wi.active_task.id
                if wid == "pychron.spectrometer":
                    windows.append(wi)
                    names.append("Spectrometer")
                elif wid == "pychron.extraction_line":
                    windows.append(wi)
                    names.append("Extraction Line")

        if windows:
            is_are, them = "is", "it"
            sing_plural = ""
            if len(windows) > 1:
                is_are, them = "are", "them"
                sing_plural = "s"

            msg = "{} window{} {} open. Is it ok to close {}?".format(
                ",".join(names), sing_plural, is_are, them
            )

            if self.confirmation_dialog(msg):
                for wi in windows:
                    wi.close()

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _active_editor_changed(self):
        if self.active_editor:
            self.manager.experiment_factory.edit_enabled = True
            self.manager.experiment_queue = self.active_editor.queue
            self.manager.executor.sync_active_context(
                editor=self.active_editor,
                queue=self.active_editor.queue,
                queues=[ei.queue for ei in self.editor_area.editors],
            )
            self._show_pane(self.experiment_factory_pane)
        else:
            self.manager.experiment_factory.edit_enabled = False
            self.manager.executor.sync_active_context(
                editor=None, queue=None, queues=[ei.queue for ei in self.editor_area.editors]
            )

    @on_trait_change("manager:experiment_queue:changed")
    def _handle_queue_change(self, obj, name, old, new):
        if self.loading_manager:
            runs = obj.cleaned_automated_runs
            self.loading_manager.set_loaded_runs(runs)

    @on_trait_change("loading_manager:group_positions")
    def _update_group_positions(self, new):
        # if not new:
        # ef = self.manager.experiment_factory
        # rf = ef.run_factory
        #
        #     rf.position = ''
        #
        # else:
        pos = self.loading_manager.selected_positions
        self._update_selected_positions(pos)

    @on_trait_change("loading_manager:selected_positions")
    def _update_selected_positions(self, new):
        ef = self.manager.experiment_factory
        if new:
            ef.selected_positions = new
            rf = ef.run_factory

            nn = new[0]

            rf.selected_irradiation = nn.irradiation
            rf.selected_level = nn.level
            rf.labnumber = nn.identifier

            # filter rows that dont match the first rows labnumber
            ns = [str(ni.position) for ni in new if ni.identifier == nn.identifier]

            n = len(ns)
            if n > 1 and abs(int(ns[0]) - int(ns[-1])) == n - 1:
                rf.position = "{}-{}".format(ns[0], ns[-1])
            else:
                rf.position = str(ns[0])

    @on_trait_change("manager:experiment_factory:extract_device")
    def _handle_extract_device(self, new):
        if new:
            if self.window:
                app = self.window.application
                ed = convert_extract_device(new)
                man = app.get_service(ILaserManager, 'name=="{}"'.format(ed))
                if man:
                    if self.laser_control_client_pane:
                        self.laser_control_client_pane.model = man

        if new == FUSIONS_UV:
            if self.active_editor and not isinstance(self.active_editor, UVExperimentEditor):
                editor = UVExperimentEditor()

                ms = self.manager.experiment_factory.queue_factory.mass_spectrometer
                editor.new_queue(mass_spectrometer=ms)
                editor.dirty = False

                # print self.active_editor
                # ask user to copy runs into the new editor
                ans = self.active_editor.queue.cleaned_automated_runs
                if ans:
                    if self.confirmation_dialog("Copy runs to the new UV Editor?"):
                        # editor.queue.executed_runs=self.active_editor.queue.executed_runs
                        editor.queue.automated_runs = self.active_editor.queue.automated_runs

                        # self.warning_dialog('Copying runs not yet implemented')

                self.active_editor.close()

                self._open_editor(editor)
                if not self.manager.executor.is_alive():
                    self.manager.executor.executable = False

    @on_trait_change("manager:experiment_factory:queue_factory:load_name")
    def _update_load(self, new):
        lm = self.loading_manager
        self.debug("load_name changed={} {}".format(new, lm))
        if lm is not None:
            lm.set_load_by_name(new)
            if lm.canvas:
                lm.canvas.editable = False

    @on_trait_change("active_editor:queue:refresh_blocks_needed")
    def _update_blocks(self):
        self.manager.experiment_factory.run_factory.load_run_blocks()

    @on_trait_change("editor_area:editors[]")
    def _update_editors(self, new) -> None:
        self.debug("_update_editors start n={}".format(len(new)))
        qs = [ei.queue for ei in new]
        self.manager.experiment_queues = qs
        self.debug("_update_editors set manager.experiment_queues")
        # Mirror open queues onto the executor so panes (e.g. StatsPane) can
        # recalculate even when the executor is idle.
        try:
            self.manager.executor.experiment_queues = qs
            self.debug("_update_editors set executor.experiment_queues")
        except Exception:
            self.debug_exception()
            pass

    @on_trait_change("manager:executor:measuring_run:plot_panel")
    def _update_plot_panel(self, new):
        if new is not None:
            self.isotope_evolution_pane.plot_panel = new

    @on_trait_change("manager:executor:run_completed")
    def _update_run_completed(self, new):
        # self._publish_notification(new)
        self.debug(
            "experiment_task run_completed run={} identifier={} active_editor={} editors={}".format(
                getattr(new, "runid", None),
                getattr(new, "identifier", None),
                type(self.active_editor).__name__ if self.active_editor is not None else None,
                len(self.editor_area.editors) if self.editor_area else 0,
            )
        )

        load_name = self.manager.executor.experiment_queue.load_name
        if load_name:
            self._update_load(load_name)

    @on_trait_change("manager:add_queues_flag")
    def _add_queues(self, new):
        self.debug("add_queues_flag trigger n={}".format(self.manager.add_queues_count))
        for _i in range(new):
            self.new()

    @on_trait_change("manager:activate_editor_event")
    def _set_active_editor(self, new):
        for ei in self.editor_area.editors:
            if id(ei.queue) == new:
                try:
                    self.editor_area.activate_editor(ei)
                except AttributeError:
                    pass
                break

    def execute(self):
        # self.debug('execute event {} {}'.format(id(self), id(obj))
        if globalv.experiment_debug:
            if not self.confirmation_dialog(
                "The Experiment Debug global flag is set. Are you sure you want to "
                "continue? If you have do not know what this means you likely do not want "
                "to continue and should contact an expert."
            ):
                return

        if self.editor_area.editors:
            try:
                # this method is error prone. just wrap in a try statement for now
                self._close_external_windows()
            except AttributeError:
                pass

            # bind the window control to the notification manager
            # if self.window:
            #     self.manager.executor.notification_manager.parent = self.window.control

            for ei in self.editor_area.editors:
                self._backup_editor(ei)

            qs = [ei.queue for ei in self.editor_area.editors if ei != self.active_editor]

            if self.active_editor:
                qs.insert(0, self.active_editor.queue)

            self.manager.executor.sync_active_context(
                editor=self.active_editor,
                queue=self.active_editor.queue if self.active_editor else None,
                queues=qs,
            )

            if self.manager.execute_queues(qs):
                # self._show_pane(self.wait_pane)
                self._set_last_experiment(self.active_editor.path)
            else:
                self.warning("experiment queue did not start properly")

    @on_trait_change("manager:executor:autoplot_event")
    def _handle_autoplot(self, new):
        if new:
            self.debug(
                "experiment_task autoplot_event run={} identifier={} editors_before={}".format(
                    getattr(new, "runid", None),
                    getattr(new, "identifier", None),
                    len(self.editor_area.editors) if self.editor_area else 0,
                )
            )
            self.debug(
                "experiment_task autoplot suppressed_for_stability run={} identifier={}".format(
                    getattr(new, "runid", None), getattr(new, "identifier", None)
                )
            )
            return

            editor = self._new_autoplot_editor(new)
            ans = self._get_autoplot_analyses(new)
            self.debug(
                "experiment_task autoplot analyses_loaded={} editor_type={} editor_id={}".format(
                    len(ans) if ans is not None else None,
                    type(editor).__name__ if editor is not None else None,
                    id(editor) if editor is not None else None,
                )
            )
            editor.set_items(ans)

            self._open_editor(editor)
            self.debug(
                "experiment_task autoplot editor_opened editor_type={} editors_after={}".format(
                    type(editor).__name__ if editor is not None else None,
                    len(self.editor_area.editors) if self.editor_area else 0,
                )
            )

            fs = [e for e in self.iter_editors(FigureEditor)]

            # Conservative reliability guard:
            # repeated figure-editor disposal appears to line up with intermittent
            # post-run Qt crashes on hover/focus, so leave older autoplot editors
            # open while we stabilize the lifecycle.
            if len(fs) > 5:
                fs = sorted(fs, key=lambda x: x.last_update)
                self.debug(
                    "experiment_task autoplot retaining_old_editors count={} oldest_type={} oldest_id={}".format(
                        len(fs),
                        type(fs[0]).__name__ if fs else None,
                        id(fs[0]) if fs else None,
                    )
                )

    def _get_autoplot_analyses(self, new):
        dvc = self.window.application.get_service(DVC_PROTOCOL)
        db = dvc.db
        ans, _ = db.get_labnumber_analyses(new.identifier)
        return dvc.make_analyses(ans)

    def _new_autoplot_editor(self, new):
        from pychron.pipeline.plot.editors.figure_editor import FigureEditor

        for editor in self.editor_area.editors:
            if isinstance(editor, FigureEditor):
                if new.identifier == editor.identifier:
                    self.debug(
                        "experiment_task autoplot reusing_editor editor_type={} editor_id={} identifier={}".format(
                            type(editor).__name__, id(editor), new.identifier
                        )
                    )
                    break
        else:
            if is_special(new.identifier):
                from pychron.pipeline.plot.editors.series_editor import SeriesEditor

                editor = SeriesEditor()
            elif new.step:
                from pychron.pipeline.plot.editors.spectrum_editor import SpectrumEditor

                editor = SpectrumEditor()
            else:
                from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor

                editor = IdeogramEditor()

            editor.identifier = new.identifier
            self.debug(
                "experiment_task autoplot created_editor editor_type={} editor_id={} identifier={}".format(
                    type(editor).__name__, id(editor), new.identifier
                )
            )

        editor.last_update = time.time()
        return editor

    @on_trait_change("manager:executor:show_conditionals_event")
    def _handle_show_conditionals(self):
        self._show_pane(self.conditionals_pane)

    @on_trait_change("manager:executor:[measuring,extracting]")
    def _handle_measuring(self, name, new):
        if new:
            if name == "measuring":
                self._show_pane(self.isotope_evolution_pane)
                # elif name == 'extracting':
                #     self._show_pane(self.wait_pane)

    @on_trait_change("active_editor:queue:dclicked")
    def _edit_event(self):
        p = self.experiment_factory_pane
        self._show_pane(p)

    @on_trait_change("manager:[save_event, executor:auto_save_event]")
    def _save_queue(self):
        self.save()

    @on_trait_change("active_editor:dirty")
    def _update_active_editor_dirty(self, new):
        if new and self.manager:
            self.manager.executor.executable = False
            # if self.active_editor:
            #     if self.active_editor.dirty:
            #         if self.manager:
            #             self.manager.executor.executable = False

    # ===============================================================================
    # default/factory
    # ===============================================================================
    def _manager_default(self):
        from pychron.envisage.initialization.initialization_parser import (
            InitializationParser,
        )

        ip = InitializationParser()
        plugin = ip.get_plugin("Experiment", category="general")
        mode = ip.get_parameter(plugin, "mode")

        # proto = 'pychron.database.isotope_database_manager.IsotopeDatabaseManager'
        # iso_db_man = self.application.get_service(proto)
        # experimentor.iso_db_man = iso_db_man

        proto = "pychron.dvc.dvc.DVC"
        dvc = self.application.get_service(proto)
        # experimentor.dvc = dvc

        experimentor = Experimentor(application=self.application, mode=mode, dvc=dvc)

        experimentor.executor.set_managers()
        experimentor.executor.bind_preferences()
        experimentor.executor.add_event(*self.events)

        return experimentor

    def _pattern_maker_view_factory(self):
        from pychron.lasers.pattern.pattern_maker_view import PatternMakerView

        return PatternMakerView()

    def _loading_manager_default(self):
        lm = self.window.application.get_service("pychron.loading.loading_manager.LoadingManager")
        if lm:
            dvc = self.window.application.get_service(DVC_PROTOCOL)
            lm.trait_set(db=dvc.db, show_group_positions=True)
            lm.setup()
            return lm

    def _default_directory_default(self):
        return paths.experiment_dir

    def _default_layout_default(self) -> TaskLayout:
        return TaskLayout(
            left=Splitter(
                PaneItem("pychron.wait", height=150),
                Tabbed(
                    PaneItem(
                        "pychron.experiment.factory",
                    ),
                    PaneItem("pychron.experiment.isotope_evolution"),
                ),
                orientation="vertical",
            ),
            right=Splitter(
                Tabbed(
                    PaneItem("pychron.experiment.stats", height=220),
                    PaneItem("pychron.console"),
                    PaneItem("pychron.experiment.timeseries"),
                    PaneItem("pychron.experiment.conditionals"),
                    PaneItem("pychron.experiment.connection_status"),
                    PaneItem("pychron.experiment.explanation"),
                ),
                PaneItem("pychron.extraction_line.canvas_dock", height=500, width=700),
                orientation="vertical",
            ),
            top=PaneItem("pychron.experiment.controls"),
        )

    def _tool_bars_default(self) -> list[SToolBar]:
        return [SToolBar(ToggleAutomatedValveConfirmationAction())]


# ============= EOF =============================================
