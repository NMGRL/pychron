#===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import TaskLayout, PaneItem, Tabbed
from traits.api import List, Button, Instance, Enum

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.envisage.resources import icon
from pychron.processing.export.export_spec import ExportSpec
from pychron.processing.export.exporter import Exporter, XMLExporter, MassSpecExporter
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.browser.panes import BrowserPane
from pychron.processing.tasks.export.panes import ExportCentralPane, DestinationPane


class ExportAction(TaskAction):
    method = 'do_export'
    image = icon('')
    name = 'Export'


class ExportTask(AnalysisEditTask, BrowserMixin):
    id = 'pychron.export'
    export_analyses = List
    name = 'Export'

    append_button = Button
    replace_button = Button
    export_button = Button

    kind = Enum('MassSpec', 'XML')
    exporter = Instance(Exporter)

    tool_bars = [SToolBar(ExportAction())]

    def do_export(self):
        if self.export_analyses:
            if self.exporter.start_export():
                n = len(self.export_analyses)
                prog = self.manager.open_progress(n)
                for ei in self.export_analyses:
                    self._export_analysis(ei, prog)
                prog.close()

    def _exporter_default(self):
        return MassSpecExporter()

    def _kind_changed(self):
        if self.kind == 'MassSpec':
            self.exporter = MassSpecExporter()
        else:
            self.exporter = XMLExporter()

    def _export_analysis(self, ai, prog):
        # db=self.manager.db
        # with db.session_ctx():
        # dest=self.destination
        espec = self._make_export_spec(ai)
        self.exporter.add(espec)
        prog.change_message('Export analysis {}'.format(ai.record_id))

    def _make_export_spec(self, ai):
        ai = self.manager.make_analysis(ai, use_cache=False)

        # rs_name, rs_text=assemble_script_blob()
        rs_name, rs_text = '', ''
        rid = ai.record_id

        exp = ExportSpec(runid=rid,
                         runscript_name=rs_name,
                         runscript_text=rs_text,
                         mass_spectrometer=ai.mass_spectrometer.capitalize(),
                         isotopes=ai.isotopes)

        exp.load_record(ai)
        return exp

    def _append_button_fired(self):
        s = self._get_selected_analyses()
        if s:
            self.export_analyses.extend(s)

    def _replace_button_fired(self):
        s = self._get_selected_analyses()
        if s:
            self.export_analyses = s

    def create_dock_panes(self):
        self.browser_pane = BrowserPane(model=self)
        return [self.browser_pane,
                DestinationPane(model=self)]

    def create_central_pane(self):
        return ExportCentralPane(model=self)

    def _default_layout_default(self):
        return TaskLayout(left=Tabbed(PaneItem('pychron.browser'),
                                      PaneItem('pychron.export.destination')))


#============= EOF =============================================

