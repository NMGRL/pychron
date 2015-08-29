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
from pyface.tasks.action.schema import SToolBar
from pyface.ui.qt4.tasks.advanced_editor_area_pane import EditorWidget
from traits.api import Any, Instance, on_trait_change
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter, VSplitter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.editor_task import EditorTask
from pychron.spectrometer.tasks.editor import PeakCenterEditor, ScanEditor, CoincidenceEditor
from pychron.spectrometer.tasks.spectrometer_actions import StopScanAction
from pychron.spectrometer.tasks.spectrometer_panes import ControlsPane, \
    ReadoutPane, IntensitiesPane, RecordControlsPane, ScannerPane


class SpectrometerTask(EditorTask):
    scan_manager = Any
    name = 'Scan'
    id = 'pychron.spectrometer'
    _scan_editor = Instance(ScanEditor)
    tool_bars = [SToolBar(StopScanAction(),)]

    def stop_scan(self):
        self.debug('stop scan fired')
        editor = self.active_editor
        if editor:
            if isinstance(editor, ScanEditor):
                editor.stop()

    def do_coincidence(self):
        es = [int(e.name.split(' ')[-1])
              for e in self.editor_area.editors
              if isinstance(e, CoincidenceEditor)]

        i = max(es) + 1 if es else 1
        man = self.scan_manager.ion_optics_manager
        name = 'Coincidence {:02d}'.format(i)

        if man.setup_coincidence():
            self._open_editor(CoincidenceEditor(model=man.coincidence, name=name))
            man.do_coincidence_scan()

    def do_peak_center(self):
        es = [int(e.name.split(' ')[-1])
              for e in self.editor_area.editors
              if isinstance(e, PeakCenterEditor)]

        i = max(es) + 1 if es else 1

        man = self.scan_manager.ion_optics_manager
        name = 'Peak Center {:02d}'.format(i)
        if man.setup_peak_center(new=True, standalone_graph=False):
            self._on_peak_center_start()

            self._open_editor(PeakCenterEditor(model=man.peak_center,
                                               name=name))

            man.do_peak_center(confirm_save=True, warn=True,
                               message='manual peakcenter',
                               on_end=self._on_peak_center_end)

    def _on_peak_center_start(self):
        self.scan_manager.log_events_enabled = False
        self.scan_manager.scan_enabled = False
        self.scan_manager.stop_scan()

    def _on_peak_center_end(self):
        self.scan_manager.log_events_enabled = True
        self.scan_manager.scan_enabled = True
        self.scan_manager.reset_scan_timer()

    def send_configuration(self):
        self.scan_manager.spectrometer.send_configuration()

    def prepare_destroy(self):
        for e in self.editor_area.editors:
            if hasattr(e, 'stop'):
                e.stop()

        self.scan_manager.prepare_destroy()
        super(SpectrometerTask, self).prepare_destroy()

    # def activated(self):
    # self.scan_manager.activate()
    # self._scan_factory()
    # super(SpectrometerTask, self).activated()

    def create_dock_panes(self):
        panes = [
            ControlsPane(model=self.scan_manager),
            RecordControlsPane(model=self.scan_manager),
            ScannerPane(model=self.scan_manager),
            ReadoutPane(model=self.scan_manager),
            IntensitiesPane(model=self.scan_manager)]

        panes = self._add_canvas_pane(panes)
        return panes

    # def _active_editor_changed(self, new):
    # if not new:
    #         try:
    #             self._scan_factory()
    #         except AttributeError:
    #             pass

    def _scan_factory(self):
        sim = self.scan_manager.spectrometer.simulation
        name = 'Scan (Simulation)' if sim else 'Scan'
        # self._open_editor(ScanEditor(model=self.scan_manager, name=name))
        # print 'asdfas', self.editor_area.control
        # print [e for e in self.editor_area.control.children() if isinstance(e, EditorWidget)]
        # super(SpectrometerTask, self).activated()

        se = ScanEditor(model=self.scan_manager, name=name)
        self._open_editor(se)

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                PaneItem('pychron.spectrometer.controls'),
                orientation='vertical'),
            right=VSplitter(PaneItem('pychron.spectrometer.intensities'),
                            PaneItem('pychron.spectrometer.readout')))

        # def create_central_pane(self):

        # g = ScanPane(model=self.scan_manager)
        # return g

    @on_trait_change('scan_manager:scanner:new_scanner')
    def _handle_scan_event(self):
        sim = self.scan_manager.spectrometer.simulation
        name = 'Magnet Scan (Simulation)' if sim else 'Magnet Scan'

        editor = next((e for e in self.editor_area.editors if e.id == 'pychron.scanner'), None)
        if editor is not None:
            self.scan_manager.scanner.reset()
        else:
            editor = ScanEditor(model=self.scan_manager.scanner, name=name, id='pychron.scanner')
            self._open_editor(editor, activate=False)
            self.split_editors(0, 1, h2=300, orientation='vertical')

        self.activate_editor(editor)

    @on_trait_change('window:opened')
    def _opened(self):
        self.scan_manager.activate()

        self._scan_factory()
        ee = [e for e in self.editor_area.control.children() if isinstance(e, EditorWidget)][0]
        # print int(ee.features())
        # ee.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        # print int(ee.features())
        # ee.update_title()

# ============= EOF =============================================
