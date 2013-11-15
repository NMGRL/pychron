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
from pyface.image_resource import ImageResource
from pyface.tasks.action.task_action import TaskAction
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths


class AnalysisEditAction(TaskAction):
    task_id = 'pychron.analysis_edit'
    #     def _create_window(self, app):
    # #         win = None
    #         # search other windows
    #         task = app.open_task(self.task_id)
    #         return task.window
    #
    def perform(self, event):
        app = event.task.window.application
        _id = self.task_id
        task = app.open_task(self.task_id)
        self.task = task

        super(AnalysisEditAction, self).perform(event)


class DatabaseSaveAction(TaskAction):
    name = 'Database Save'
    description = 'Save current changes to the database'
    method = 'save_to_db'
    image = ImageResource(name='database_save.png',
                          search_path=paths.icon_search_path)


class FindAssociatedAction(TaskAction):
    name = 'Find Associated'
    description = 'Find associated analyses'
    method = 'find_associated_analyses'
    image = ImageResource(name='find.png',
                          search_path=paths.icon_search_path)


class TagAction(TaskAction):
    name = 'Tag...'
    accelerator = 'Ctrl+Shift+t'
    method = 'set_tag'


class FluxAction(AnalysisEditAction):
    name = 'Flux...'
    accelerator = 'Ctrl+g'
    method = 'new_flux'
    task_id = 'pychron.analysis_edit.flux'


class BlankEditAction(AnalysisEditAction):
    name = 'Blanks...'
    accelerator = 'Ctrl+B'
    method = 'new_blank'
    task_id = 'pychron.analysis_edit.blanks'


# class SeriesAction(AnalysisEditAction):
#     name = 'Series...'
#     accelerator = 'Ctrl+L'
#     method = 'new_series'
#     task_id = 'pychron.analysis_edit.series'

class IsotopeEvolutionAction(AnalysisEditAction):
    name = 'Isotope Evolution...'
    accelerator = 'Ctrl+k'
    method = 'new_isotope_evolution'
    task_id = 'pychron.analysis_edit.isotope_evolution'


class RefitIsotopeEvolutionAction(AnalysisEditAction):
    name = 'Refit Isotope Evolution...'
    accelerator = 'Ctrl+Shift+f'
    method = 'refit_isotopes'
    task_id = 'pychron.analysis_edit.isotope_evolution'


class ICFactorAction(AnalysisEditAction):
    name = 'IC Factor...'
    accelerator = 'Ctrl+shift+i'
    method = 'new_ic_factor'
    task_id = 'pychron.analysis_edit.ic_factor'


class DiscriminationAction(AnalysisEditAction):
    name = 'Discrimination...'
    accelerator = 'Ctrl+shift+d'
    #method = 'new_ic_factor'
    task_id = 'pychron.analysis_edit.discrimination'


class BatchEditAction(AnalysisEditAction):
    name = 'Batch Edit...'
    #accelerator = 'Ctrl+Shift+e'
    task_id = 'pychron.analysis_edit.batch'


class SmartBatchEditAction(AnalysisEditAction):
    name = 'Smart Batch Edit...'
    accelerator = 'Ctrl+Shift+e'
    task_id = 'pychron.analysis_edit.smart_batch'


class SCLFTableAction(AnalysisEditAction):
    name = 'SCLF Table...'
    accelerator = 'Ctrl+t'
    method = 'new_sclf_table'
    task_id = 'pychron.processing.publisher'


#============= EOF =============================================
