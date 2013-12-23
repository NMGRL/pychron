#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
from pychron.processing.tasks.interpreted_age.interpreted_age_editor import InterpretedAgeEditor


class SavePDFTablesAction(TaskAction):
    name='Save Tables'
    method='save_pdf_tables'


class OpenTableAction(TaskAction):
    name='Open Table'
    method='open_table'

class InterpretedAgeTask(BaseBrowserTask):
    id = 'pychron.processing.interpreted_age'
    tool_bars = [SToolBar(SavePDFTablesAction(),
                          OpenTableAction())]

    def open_table(self):
        # p=self.open_file_dialog()
        p = '/Users/ross/Sandbox/interpreted_age.yaml'
        if p:
            self.active_editor.open_table_recipe(p)

    def save_pdf_tables(self):
        # p=self.save_file_dialog()
        p='/Users/ross/Sandbox/interpreted_age.pdf'
        if p:
            self.active_editor.save_pdf_tables(p)

        self.view_pdf(p)
        self.view_pdf('/Users/ross/Sandbox/interpreted_age.step_heat_data.pdf')

    def create_dock_panes(self):
        panes = [self._create_browser_pane(analyses_defined='0')]

        return panes

    def _selected_samples_changed(self):
        if not self.active_editor:
            editor=InterpretedAgeEditor(processor=self.manager)
            self._open_editor(editor)

        self.active_editor.set_samples(self.selected_samples)
#============= EOF =============================================

