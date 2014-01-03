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
from pyface.tasks.task_layout import TaskLayout, PaneItem
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
from pychron.processing.tasks.interpreted_age.actions import SavePDFTablesAction, SaveInterpretedAgeGroupAction, OpenTableAction
from pychron.processing.tasks.interpreted_age.interpreted_age_editor import InterpretedAgeEditor
from pychron.processing.tasks.interpreted_age.save_group_dialog import SaveGroupDialog


class InterpretedAgeTask(BaseBrowserTask):
    name = 'Interpreted Ages'
    id = 'pychron.processing.interpreted_age'
    tool_bars = [SToolBar(SavePDFTablesAction(),
                          OpenTableAction()),
                 SToolBar(SaveInterpretedAgeGroupAction())]

    def save_interpreted_age_group(self):

        if self.active_editor:
            if self.active_editor.interpreted_ages:

                sgd = SaveGroupDialog(projects=self.projects)
                if self.selected_projects:
                    sgd.selected_project=self.selected_projects[-1]

                info = sgd.edit_traits(kind='livemodal')
                if info.result:
                    name=sgd.name
                    project=sgd.selected_project.name

                    name = 'Foo'
                    project = 'Minna Bluff'

                    if name and project:
                        self.active_editor.save_group(name, project)

    def open_table(self):
        # p=self.open_file_dialog()
        # p = '/Users/ross/Sandbox/interpreted_age.yaml'
        # if p:
        #     self.active_editor.open_table_recipe(p)
        if self.active_editor:
            self.active_editor.open_group()

    def save_pdf_tables(self):
        # p=self.save_file_dialog()
        p = '/Users/ross/Sandbox/interpreted_age.pdf'
        if p:
            self.active_editor.save_pdf_tables(p)

        self.view_pdf(p)
        self.view_pdf('/Users/ross/Sandbox/interpreted_age.step_heat_data.pdf')

    def create_dock_panes(self):
        panes = [self._create_browser_pane(analyses_defined='0')]

        return panes

    def _selected_samples_changed(self):
        if not self.active_editor:
            editor = InterpretedAgeEditor(processor=self.manager)
            self._open_editor(editor)

        self.active_editor.set_samples(self.selected_samples)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.browser'))

#============= EOF =============================================

