# ===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import TaskLayout, PaneItem, Tabbed
from traits.api import List, Button, Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.processing.export.export_manager import ExportManager
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.export.panes import ExportCentralPane


class ExportAction(TaskAction):
    method = 'do_export'
    image = icon('')
    name = 'Export'


class ExportTask(AnalysisEditTask):
    name = 'Export'
    id = 'pychron.export'

    export_analyses = List
    exported_analyses = List
    #
    #     append_button = Button
    #     replace_button = Button
    #     export_button = Button
    export_manager = Instance(ExportManager)
    tool_bars = [SToolBar(ExportAction())]

    #     def _dclicked_sample_changed(self):
    #         ans = [ai for ai in self.analysis_table.analyses if ai not in self.export_analyses]
    #         self.export_analyses.extend(ans)
    #
    
    def activated(self):
        super(ExportTask, self).activated()
        ans = self.browser_model.analysis_table.analyses

        self.unknowns_pane.items = self.manager.make_analyses(ans, calculate_age=True)

    def _append_replace_unknowns(self, is_append, items=None):
        if not items:
            ans = None
            if is_append:
                ans = self.export_analyses
            items = self._get_selected_analyses(ans)

        if items:
            if is_append:
                pitems = self.unknowns_pane.items
                items = [ai for ai in items
                         if ai not in pitems]

                items = self.manager.make_analyses(items, calculate_age=True)
                pitems.extend(items)
                # self.export_analyses.extend(items)
            else:
                items = self.manager.make_analyses(items, calculate_age=True)
                self.unknowns_pane.items = items
                # self.export_analyses = items
            #

    def _export_manager_default(self):
        return ExportManager(manager=self.manager)

    #
    def do_export(self):
        if self.unknowns_pane.items:
            self.export_manager.export(self.unknowns_pane.items)

        #     def _append_button_fired(self):
        #         s = self._get_selected_analyses()
        #         if s:
        #             self.export_analyses.extend(s)
        #
        #     def _replace_button_fired(self):
        #         s = self._get_selected_analyses()
        #         if s:
        #             self.export_analyses = s
        #
        #     def create_dock_panes(self):
        #         bp=self._create_browser_pane()
        #         # self.browser_pane = BrowserPane(model=self)
        #         return [bp,
        #                 DestinationPane(model=self.export_manager)]
        #

    def create_central_pane(self):
        return ExportCentralPane(model=self.export_manager)

#
#     def _default_layout_default(self):
#         return TaskLayout(left=Tabbed(PaneItem('pychron.browser',width=300),
#                                       PaneItem('pychron.export.destination')))
#
#
# # ============= EOF =============================================
#
