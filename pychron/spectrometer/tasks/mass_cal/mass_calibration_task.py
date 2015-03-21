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
from pyface.tasks.task_layout import TaskLayout, PaneItem, VSplitter
from traits.api import Any, Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.spectrometer.mass_cal.mass_calibrator import MassCalibratorScan
from pychron.spectrometer.tasks.mass_cal.editor import MassCalibrationEditor
from pychron.spectrometer.tasks.mass_cal.panes import MassCalibrationTablePane, \
    MassCalibrationsPane, MassCalibrationControlPane


class MassCalibrationTask(BaseEditorTask):
    name = 'Mass Calibration'
    spectrometer_manager = Any

    scanner = Instance(MassCalibratorScan)

    def _active_editor_changed(self):
        if self.active_editor:
            self.scanner.graph = self.active_editor.graph
            self.scanner.setup_graph()

    def _scanner_default(self):
        spec = self.spectrometer_manager.spectrometer


        s = MassCalibratorScan(spectrometer=spec,
                               db=IsotopeDatabaseManager())
        if spec.simulation:
            s.integration_time =0.065536
        s.verbose=True

        return s

    def activated(self):
        editor = MassCalibrationEditor()
        self._open_editor(editor)

    def create_dock_panes(self):
        return [MassCalibrationTablePane(model=self),
                MassCalibrationsPane(model=self),
                MassCalibrationControlPane(model=self)]

    def _default_layout_default(self):
        return TaskLayout(left=VSplitter(
            PaneItem('pychron.mass_calibration.cal_points'),
            PaneItem('pychron.mass_calibration.controls')))


# ============= EOF =============================================

