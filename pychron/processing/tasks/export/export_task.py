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
from traits.api import List, Button, Instance

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.envisage.resources import icon
from pychron.processing.export.export_manager import ExportManager
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
    export_manager=Instance(ExportManager)
    tool_bars = [SToolBar(ExportAction())]

    def _export_manager_default(self):
        return ExportManager(manager=self.manager)

    def do_export(self):
        if self.export_analyses:
            self.export_manager.export(self.export_analyses)

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

