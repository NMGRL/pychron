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
# from pyface.tasks.action.task_action import TaskAction
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.envisage.tasks.actions import PTaskAction as TaskAction


class AnalysisEditAction(TaskAction):
    task_id = 'pychron.processing'
    #     def _create_window(self, app):
    # #         win = None
    #         # search other windows
    #         task = app.open_task(self.task_id)
    #         return task.window
    #
    def perform(self, event):
        app = event.task.window.application
        task = app.open_task(self.task_id)
        self.task = task

        super(AnalysisEditAction, self).perform(event)


class DatabaseSaveAction(TaskAction):
    name = 'Database Save'
    dname = 'Database Save'
    description = 'Save current changes to the database'
    method = 'save_to_db'
    image = icon('database_save')


class BinAnalysesAction(TaskAction):
    name = 'Bin'
    description = ''
    method = 'bin_analyses'
    image = icon('database_save')


class FindAssociatedAction(TaskAction):
    name = 'Find Associated'
    description = 'Find associated analyses'
    method = 'find_associated_analyses'
    image = icon('find')


class TagAction(TaskAction):
    name = 'Tag...'
    dname = 'Tag'
    # accelerator = 'Ctrl+Shift+t'
    method = 'set_tag'
    image = icon('tag-blue-add')
    id = 'pychron.tag'


class DataReductionTagAction(TaskAction):
    name = 'Data Reduction Tag...'
    dname = 'Data Reduction Tag'
    method = 'set_data_reduction_tag'


class SelectDataReductionTagAction(TaskAction):
    name = 'Select Data Reduction Tag...'
    dname = 'Select Data Reduction Tag'
    method ='select_data_reduction_tag'


class FluxAction(AnalysisEditAction):
    name = 'Flux...'
    dname = 'Flux'
    # accelerator = 'Ctrl+g'
    method = 'new_flux'
    task_id = 'pychron.processing.flux'
    id = 'pychron.flux'


class BlankEditAction(AnalysisEditAction):
    name = 'Blanks...'
    dname = 'Blanks'
    # accelerator = 'Ctrl+B'
    method = 'new_blank'
    # task_id = 'pychron.processing.blanks'
    task_id = 'pychron.processing.reduction'
    id = 'pychron.blank'


class ICFactorAction(AnalysisEditAction):
    name = 'IC Factor...'
    dname = 'IC Factor'
    # accelerator = 'Ctrl+shift+i'
    method = 'new_ic_factor'
    task_id = 'pychron.processing.reduction'
    id = 'pychron.ic_factor'

# class SeriesAction(AnalysisEditAction):
#     name = 'Series...'
#     accelerator = 'Ctrl+L'
#     method = 'new_series'
#     task_id = 'pychron.processing.series'

class IsotopeEvolutionAction(AnalysisEditAction):
    name = 'Isotope Evolution...'
    dname = 'Isotope Evolution'
    # accelerator = 'Ctrl+k'
    method = 'new_isotope_evolution'
    task_id = 'pychron.processing.isotope_evolution'
    id = 'pychron.isotope_evolution'

class RefitIsotopeEvolutionAction(AnalysisEditAction):
    name = 'Refit Isotope Evolution...'
    accelerator = 'Ctrl+Shift+f'
    method = 'refit_isotopes'
    task_id = 'pychron.processing.isotope_evolution'





class DiscriminationAction(AnalysisEditAction):
    name = 'Discrimination...'
    dname = 'Discrimination'
    accelerator = 'Ctrl+shift+d'
    #method = 'new_ic_factor'
    task_id = 'pychron.processing.discrimination'


class BatchEditAction(AnalysisEditAction):
    name = 'Batch Edit...'
    #accelerator = 'Ctrl+Shift+e'
    task_id = 'pychron.processing.batch'


class SmartBatchEditAction(AnalysisEditAction):
    name = 'Smart Batch Edit...'
    accelerator = 'Ctrl+Shift+e'
    task_id = 'pychron.processing.smart_batch'


class SCLFTableAction(AnalysisEditAction):
    name = 'SCLF Table...'
    accelerator = 'Ctrl+t'
    method = 'new_sclf_table'
    task_id = 'pychron.processing.publisher'


# ============= EOF =============================================
