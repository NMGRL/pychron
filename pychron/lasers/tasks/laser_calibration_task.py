# ===============================================================================
# Copyright 2013 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
from pyface.tasks.action.schema import SToolBar
from traits.api import Property, Bool, Event, on_trait_change
# from traitsui.api import View, Item, TextEditor
from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.editor_task import EditorTask
from pychron.lasers.tasks.editors.pid_tuning_editor import PIDTuningEditor
from pychron.lasers.tasks.editors.power_map_editor import PowerMapEditor
from pychron.lasers.tasks.editors.power_calibration_editor import PowerCalibrationEditor
from pychron.lasers.tasks.editors.pyrometer_calibration_editor import PyrometerCalibrationEditor
from pychron.lasers.tasks.laser_actions import PyrometerCalibrationAction
from pychron.lasers.tasks.laser_calibration_panes import LaserCalibrationControlPane, \
    LaserCalibrationExecutePane
import os
from pychron.paths import paths


class BaseLaserTask(EditorTask):
    def activated(self):
        pass

    def prepare_destroy(self):
        pass


class LaserCalibrationTask(BaseLaserTask):
    id = 'pychron.laser.calibration'
    execute = Event
    execute_label = Property(depends_on='executing')
    executing = Bool

    tool_bars = [SToolBar(PyrometerCalibrationAction(), image_size=(16, 16))]


    def _get_execute_label(self):
        return 'Stop' if self.executing else 'Start'

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                PaneItem('pychron.laser_calibration.execute',
                         width=200
                ),
                PaneItem('pychron.laser_calibration.control',
                         width=200
                ),
                orientation='vertical'
            )
        )

    #     def activated(self):
    #             self.new_power_map()

    def create_dock_panes(self):
        ep = LaserCalibrationExecutePane(model=self)
        lp = LaserCalibrationControlPane()
        self.control_pane = lp
        return [lp, ep]

    def get_power_maps(self):
        ps = self.open_file_dialog(action='open files',
                                   default_directory=paths.power_map_dir
        )
        return ps

    def open_power_maps(self, ps):

    #         ps = self.open_file_dialog(action='open files',
    #                                       default_directory=paths.power_map_dir
    #                                       )
    #         p = '/Users/ross/Pychrondata_demo/data/scans/powermap-2013-07-17001.hdf5'
    #        p = '/Users/ross/Sandbox/powermap/powermap-2013-07-26005.hdf5'
    #         p = '/Users/ross/Sandbox/powermap/powermap-2013-07-27008.hdf5'
    #        p = '/Users/ross/Sandbox/powermap/Archive 2/powermap-2013-07-31001.hdf5'
    #         p = '/Users/ross/Sandbox/powermap/Archive 2/powermap-2013-07-31002.hdf5'
    #         p = '/Users/ross/Sandbox/powermap-2013-07-26005.hdf5'
        if ps:
            for p in ps:
                try:
                #                p = '/Users/ross/Sandbox/powermap/Archive 2/powermap-2013-07-31{:03n}.hdf5'.format(i)
                    editor = PowerMapEditor(
                        #                                     name='Power Map {:03n}'.format(n + 1),
                        name='Power Map {}'.format(os.path.basename(p))
                    )
                    editor.load(p)
                    self._open_editor(editor)
                except Exception:
                    self.debug('invalid power map file {}'.format(p))

    def new_power_map(self):

        n = len([ed for ed in self.editor_area.editors
                 if isinstance(ed, PowerMapEditor)])

        editor = PowerMapEditor(name='Power Map {:03d}'.format(n + 1))
        if self.active_editor:
            editor.editor = self.control_pane.editor

        self._open_editor(editor)

    def new_power_calibration(self):
        n = len([ed for ed in self.editor_area.editors
                 if isinstance(ed, PowerCalibrationEditor)])

        editor = PowerCalibrationEditor(name='Power Calibration {:03d}'.format(n + 1))
        self._open_editor(editor)

    def new_pyrometer_calibration(self):
        editor = PyrometerCalibrationEditor(name='Pyrometer Calibration')
        self._open_editor(editor)

    def new_pid_tuner(self):
        editor=PIDTuningEditor(name='PID Tuning')
        self._open_editor(editor)
    # ===============================================================================
    # handlers
    # ===============================================================================
    def execute_active_editor(self, block=False):
        if self.active_editor.do_execute(self.manager):
            self.executing = True

        if block:
            self.active_editor.block()

        #    def execute_last_editor(self, block=False):
        #        editor = self.editor_area.editors[-1]
        #        if editor.do_execute(self.manager):
        #            self.executing = True
        #
        #        if block:
        #            self.editor.block()

    def _execute_changed(self):
        if self.active_editor:
            if self.executing:
                self.active_editor.stop()
                self.executing = False
            else:
                if self.active_editor.was_executed:
                    self.new_power_map()

                self.execute_active_editor()
        else:
            self.new_power_map()
            self.execute_active_editor()


    def _active_editor_changed(self):
        if self.active_editor:
            if hasattr(self.active_editor, 'editor'):
                self.control_pane.editor = self.active_editor.editor

    @on_trait_change('active_editor:completed')
    def _update_completed(self, new):
        print 'asdf', new
        if new:
            self.executing = False
            self.active_editor.was_executed = True


# ===============================================================================
# action handlers
# ===============================================================================



# class FusionsCO2Task(FusionsTask):
#     id = 'pychron.fusions.co2'
#     name = 'Fusions CO2 Las'
#
#     def create_dock_panes(self):
#         return []
#
# class FusionsDiodeTask(FusionsTask):
#     id = 'fusions.diode'
#     name = 'Fusions Diode'
#
#     def create_dock_panes(self):
#         return []
# ============= EOF =============================================
