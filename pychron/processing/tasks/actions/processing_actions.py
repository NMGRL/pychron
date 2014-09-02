# ===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, List
from pyface.action.action import Action
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================
#============= local library imports  ==========================
# class ProcessorAction(Action):
#     def _get_processor(self, event):
#         app = event.task.window.application
#         processor = app.get_service('pychron.processing.processor.Processor')
#         return processor


#===============================================================================
# grouping
#===============================================================================
from pychron.envisage.resources import icon


class myTaskAction(TaskAction):
    task_ids = List

    def _task_changed(self):
        if self.task:
            if self.task.id in self.task_ids:
                enabled = True
                if self.enabled_name:
                    if self.object:
                        enabled = bool(self._get_attr(self.object,
                                                      self.enabled_name, False))
                if enabled:
                    self._enabled = True
            else:
                self._enabled = False

    def _enabled_update(self):
        """
             reimplement ListeningAction's _enabled_update
        """
        if self.enabled_name:
            if self.object:
                self.enabled = bool(self._get_attr(self.object,
                                                   self.enabled_name, False))
            else:
                self.enabled = False
        elif self._enabled is not None:
            self.enabled = self._enabled
        else:
            self.enabled = bool(self.object)


class FigureTaskAction(myTaskAction):
    task_ids = List(['pychron.processing.figures', ])


class GroupAction(FigureTaskAction):
    pass


class GroupSelectedAction(GroupAction):
    name = 'Group Selected'
    method = 'group_selected'
    image = icon('placeholder')


class GraphGroupSelectedAction(GroupAction):
    name = 'Graph Group Selected'
    method = 'graph_group_selected'


class GraphGroupbySampleAction(GroupAction):
    name = 'Graph Group by Sample'
    method = 'graph_group_by_sample'


#     def perform(self, event):
#         task = event.task
#         if task.id == 'pychron.processing.figures':
#             task.group_selected()

class GroupbySampleAction(GroupAction):
    name = 'Group by Sample'
    method = 'group_by_sample'
    image = icon('placeholder')


class GroupbyLabnumberAction(GroupAction):
    name = 'Group by Labnumber'
    method = 'group_by_labnumber'
    image = icon('placeholder')


class GroupbyAliquotAction(GroupAction):
    name = 'Group by Aliquot'
    method = 'group_by_aliquot'
    image = icon('placeholder')


class ClearGroupAction(GroupAction):
    name = 'Clear Grouping'
    method = 'clear_grouping'
    image = icon('placeholder')


class AnalysisAction(myTaskAction):
    task_ids = List(['pychron.processing.figures',
                     'pychron.processing.blanks',
                     'pychron.processing.isotope_evolution',
                     'pychron.processing.ic_factor',
                     'pychron.processing.flux',
                     'pychron.processing.batch',
                     'pychron.processing.discrimination'])


class MakeAnalysisGroupAction(AnalysisAction):
    name = 'Make Analysis Group'
    method = 'make_analysis_group'
    image = icon('database_add')


class DeleteAnalysisGroupAction(AnalysisAction):
    name = 'Delete Analysis Group'
    method = 'delete_analysis_group'
    image = icon('database_delete')


#===============================================================================
#
#===============================================================================
class EquilibrationInspectorAction(Action):
    name = 'Equilibration Inspector...'

    def perform(self, event):
        from pychron.processing.utils.equil import EquilibrationInspector

        eq = EquilibrationInspector()
        eq.refresh()
        app = event.task.window.application
        app.open_view(eq)


#===============================================================================
# figures
#===============================================================================
class FigureAction(Action):
    method = Str

    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.processing.figures')
        if hasattr(task, self.method):
            getattr(task, self.method)()


class XYScatterAction(FigureAction):
    name = 'XY Scatter'
    method = 'new_xy_scatter'
    accelerator = 'Ctrl+Shift+x'


class IdeogramAction(FigureAction):
    name = 'Ideogram'
    accelerator = 'Ctrl+J'
    method = 'new_ideogram'
    image = icon('histogram')


class SpectrumAction(FigureAction):
    name = 'Spectrum'
    accelerator = 'Ctrl+D'
    method = 'new_spectrum'


class SeriesAction(FigureAction):
    name = 'Series'
    accelerator = 'Ctrl+U'
    method = 'new_series'


class InverseIsochronAction(FigureAction):
    name = 'Inverse Isochron'
    method = 'new_inverse_isochron'
    accelerator = 'Ctrl+i'


class IdeogramFromFile(FigureAction):
    name = 'Ideogram'
    method = 'new_ideogram_from_file'
    accelerator = 'Ctrl+shift+j'


class SpectrumFromFile(FigureAction):
    name = 'Spectrum'
    method = 'new_spectrum_from_file'
    # accelerator = 'Ctrl+shift+d'


#===============================================================================
#
#===============================================================================
class RecallAction(Action):
    name = 'Recall'
    accelerator = 'Ctrl+R'

    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.recall')


class ConfigureRecallAction(myTaskAction):
    name = 'Configure Recall'
    method = 'configure_recall'
    image = icon('cog.png')
    task_ids = List(['pychron.recall', 'pychron.processing.figures',
                     'pychron.processing.blanks',
                     'pychron.processing.isotope_evolution',
                     'pychron.processing.ic_factor',
                     'pychron.processing.discrimination'])


class OpenInterpretedAgeAction(Action):
    name = 'Browse Interpreted Ages'

    def perform(self, event):
        app = event.task.window.application
        task = app.open_task('pychron.processing.interpreted_age')


class SetInterpretedAgeAction(FigureTaskAction):
    name = 'Set Interpreted Age...'
    #accelerator = 'Ctrl+t'
    method = 'set_interpreted_age'


class SetInterpretedAgeTBAction(FigureTaskAction):
    name = 'Set Interpreted Age'
    #accelerator = 'Ctrl+t'
    method = 'set_interpreted_age'
    image = icon('database_add.png')


class BrowseInterpretedAgeTBAction(FigureTaskAction):
    name = 'Browse Interpreted Age'
    #accelerator = 'Ctrl+t'
    method = 'browse_interpreted_age'
    image = icon('application_view_list.png')


class OpenAdvancedQueryAction(Action):
    name = 'Find Analysis...'
    image = icon('edit-find.png')

    def perform(self, event):
        app = event.task.window.application
        task = app.open_task('pychron.advanced_query')
        task.set_append_replace_enabled(False)


class ClearAnalysisCacheAction(Action):
    name = 'Clear Analysis Cache'
    image = icon('edit-clear')

    def perform(self, event=None):
        from pychron.database.isotope_database_manager import ANALYSIS_CACHE, ANALYSIS_CACHE_COUNT

        ANALYSIS_CACHE.clear()
        ANALYSIS_CACHE_COUNT.clear()


class ExportAnalysesAction(Action):
    name = 'Export Analyses...'

    def perform(self, event):
        app = event.task.window.application
        app.open_task('pychron.export')


class ModifyK3739Action(myTaskAction):
    name = 'Modify (37/39)K...'
    method = 'modify_k3739'
    task_ids = List(['pychron.processing.figures', 'pychron.recall', 'pychron.processing.isotope_evolution'])


class SplitEditorActionHor(myTaskAction):
    name = 'Split Editor Horizontal'
    task_ids = List(['pychron.processing.figures', 'pychron.recall'])
    method = 'split_editor_area_hor'


class SplitEditorActionVert(myTaskAction):
    name = 'Split Editor Vertical'
    task_ids = List(['pychron.processing.figures', 'pychron.recall'])
    method = 'split_editor_area_vert'
    image = icon('split_vertical')


class CalculationViewAction(myTaskAction):
    name = 'Calculation View'
    task_ids = ['pychron.recall', ]
    method = 'open_calculation_view'
    image = icon('window-new')


class ComprehensiveAction(myTaskAction):
    name = 'Comprehensive View'
    method = 'new_comprehensive_editor'
    task_ids = ['pychron.recall']
    image = icon('window-new')

#============= EOF =============================================

