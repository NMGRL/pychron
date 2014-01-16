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
from pychron.processing.tasks.interpreted_age.actions import SavePDFTablesAction, SaveInterpretedAgeGroupAction,\
    OpenInterpretedAgeGroupAction, SaveAsInterpretedAgeGroupAction
from pychron.processing.tasks.interpreted_age.interpreted_age_editor import InterpretedAgeEditor
from pychron.processing.tasks.interpreted_age.group_dialog import SaveGroupDialog, OpenGroupDialog


class InterpretedAgeTask(BaseBrowserTask):
    name = 'Interpreted Ages'
    id = 'pychron.processing.interpreted_age'
    tool_bars = [SToolBar(SavePDFTablesAction()),
                 SToolBar(SaveAsInterpretedAgeGroupAction(),
                          SaveInterpretedAgeGroupAction(),
                          OpenInterpretedAgeGroupAction())]

    def external_open_interpreted_age_group(self):
        self.load_projects()
        ogd = OpenGroupDialog(projects=self.projects, db=self.manager.db)
        info = ogd.edit_traits(kind='livemodal')
        if info.result:
            return ogd.get_selected_ids()

    def open_interpreted_age_group(self):
        if self.active_editor:
            ogd=OpenGroupDialog(projects=self.projects, db=self.manager.db)
            if self.selected_projects:
                ogd.selected_project = self.selected_projects[-1]

            info = ogd.edit_traits(kind='livemodal')
            if info.result:
                ids=ogd.get_selected_ids()
                if ids:
                    self.open_interpreted_age_groups(ids)

    def open_interpreted_age_groups(self, gids):
        self.active_editor.open_group(gids[0])
        for i in gids[1:]:
            editor = self._new_editor()
            editor.open_group(i)

    def save_interpreted_age_group(self):
        if self.active_editor.saved_group_id:
            self.active_editor.update_group()
        else:
            self.save_as_interpreted_age_group()

    def save_as_interpreted_age_group(self):
        if self.active_editor:
            if self.active_editor.interpreted_ages:

                sgd = SaveGroupDialog(projects=self.projects)
                if self.selected_projects:
                    sgd.selected_project = self.selected_projects[-1]

                info = sgd.edit_traits(kind='livemodal')
                if info.result:
                    name = sgd.name
                    project = sgd.selected_project.name
                    if name and project:
                        self.active_editor.save_group(name, project)

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

    def _new_editor(self):
        editor = InterpretedAgeEditor(processor=self.manager)
        self._open_editor(editor)
        return editor

    def _selected_samples_changed(self):
        if not self.active_editor:
            self._new_editor()

        self.active_editor.set_samples(self.selected_samples)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.browser'))

#============= EOF =============================================

