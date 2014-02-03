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
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================
#============= local library imports  ==========================

#============= EOF =============================================
from pychron.envisage.resources import icon


class PlotIdeogramAction(TaskAction):
    name = 'Ideogram'
    method = 'plot_ideogram'
    image = icon('file_pdf')


class SavePDFTablesAction(TaskAction):
    name = 'Save PDF Tables'
    method = 'save_pdf_tables'
    image = icon('file_pdf')


class SaveInterpretedAgeGroupAction(TaskAction):
    name = 'Save Group'
    method = 'save_interpreted_age_group'
    image = icon('database_edit')


class SaveAsInterpretedAgeGroupAction(TaskAction):
    name = 'Save As Group'
    method = 'save_as_interpreted_age_group'
    image = icon('database_add')


class OpenInterpretedAgeGroupAction(TaskAction):
    name = 'Open Group'
    method = 'open_interpreted_age_group'
    image = icon('database_go')

    def perform(self, event=None):
        app = self.task.window.application
        method = self._get_attr(self.object, self.method)
        if method:
            method()
        else:
            task = app.get_task('pychron.processing.interpreted_age', activate=False)
            gids = task.external_open_interpreted_age_group()
            if gids:
                win = task.window
                if app.is_open(win):
                    win.activate()
                else:
                    win.open()

                task.open_interpreted_age_groups(gids)


class MakeGroupFromFileAction(TaskAction):
    name = 'Group From File'
    method = 'make_group_from_file'
    image = icon('document-open-2.png')

    def perform(self, event=None):
        app = self.task.window.application
        method = self._get_attr(self.object, self.method)
        if method:
            method()
        else:
            task = app.get_task('pychron.processing.interpreted_age', activate=False)
            method = self._get_attr(task, self.method)
            if method:
                method()


class DeleteInterpretedAgeGroupAction(TaskAction):
    name = 'Delete Group'
    method = 'delete_group'
    image = icon('delete.png')

    def perform(self, event=None):
        app = self.task.window.application
        method = self._get_attr(self.object, self.method)
        if method:
            method()
        else:
            task = app.get_task('pychron.processing.interpreted_age', activate=False)
            task.external_delete_group()