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
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.processing.tasks.actions.processing_actions import myTaskAction


class AddIsoEvoAction(TaskAction):
    name = 'Iso. Evo'
    method = 'add_iso_evo'
    image = icon('chart_curve_add')



class AddDiffAction(TaskAction):
    name = 'Diff'
    method = 'add_diff'
    image = icon('edit_diff')


class EditDataAction(TaskAction):
    name = 'Edit Data'
    method = 'edit_data'
    image = icon('application-form-edit')


class DatasetAction(TaskAction):
    name = 'New Dataset'
    method = 'new_dataset'


class RatioEditorAction(TaskAction):
    name='Ratio'
    method = 'open_ratio_editor'
    image = icon('window-new')
class SummaryLabnumberAction(myTaskAction):
    name = 'Summary L# View'
    method = 'new_summary_labnumber_editor'
    task_ids = ['pychron.recall']
    image = icon('window-new')


class CalculationViewAction(myTaskAction):
    name = 'Calculation View'
    task_ids = ['pychron.recall', ]
    method = 'open_calculation_view'
    image = icon('window-new')


class SummaryProjectAction(myTaskAction):
    name = 'Summary Project View'
    method = 'new_summary_project_editor'
    task_ids = ['pychron.recall']
    image = icon('window-new')


class ContextViewAction(myTaskAction):
    name = 'Context View'
    method = 'new_context_editor'
    task_ids = ['pychron.recall']
    image = icon('window-new')
#============= EOF =============================================
