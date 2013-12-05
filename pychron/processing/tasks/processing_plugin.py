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
from envisage.ui.tasks.task_factory import TaskFactory
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.action.group import Group
from pyface.tasks.action.schema import SMenu, SGroup
#============= standard library imports ========================
#============= local library imports  ==========================

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.processing.processor import Processor
from pychron.processing.tasks.actions.import_actions import EasyImportAction
from pychron.processing.tasks.actions.easy_actions import EasyFitAction, EasyBlanksAction, EasyDiscriminationAction, EasyFiguresAction, EasyTablesAction
from pychron.processing.tasks.processing_actions import IdeogramAction, \
    RecallAction, SpectrumAction, \
    EquilibrationInspectorAction, InverseIsochronAction, GroupSelectedAction, \
    GroupbyAliquotAction, GroupbyLabnumberAction, ClearGroupAction, \
    SeriesAction, SetInterpretedAgeAction

from pychron.processing.tasks.actions.edit_actions import BlankEditAction, \
    FluxAction, IsotopeEvolutionAction, ICFactorAction, \
    BatchEditAction, TagAction, DatabaseSaveAction, DiscriminationAction
from pychron.processing.tasks.isotope_evolution.actions import CalcOptimalEquilibrationAction
from pychron.processing.tasks.processing_preferences import ProcessingPreferencesPane
#from pychron.processing.tasks.browser.browser_task import BrowserTask
from pyface.message_dialog import warning


class ProcessingPlugin(BaseTaskPlugin):
    def _service_offers_default(self):
        process_so = self.service_offer_factory(
            protocol=Processor,
            factory=self._processor_factory)

        return [process_so]

    def start(self):
        try:
            import xlwt
        except ImportError:
            warning(None, '''"xlwt" package not installed. 
            
Install to enable MS Excel export''')

    def _make_task_extension(self, actions, **kw):
        def make_schema(args):
            if len(args) == 3:
                mkw = {}
                i, f, p = args
            else:
                i, f, p, mkw = args
            return SchemaAddition(id=i, factory=f, path=p, **mkw)

        return TaskExtension(actions=[make_schema(args)
                                      for args in actions], **kw)

    def _my_task_extensions_default(self):
        def figure_group():
            return Group(
                SpectrumAction(),
                IdeogramAction(),
                InverseIsochronAction(),
                SeriesAction(),
                )

        def data_menu():
            return SMenu(id='Data', name='Data')

        def grouping_group():
            return Group(GroupSelectedAction(),
                         GroupbyAliquotAction(),
                         GroupbyLabnumberAction(),
                         ClearGroupAction())

        def reduction_group():
            return Group(IsotopeEvolutionAction(),
                         BlankEditAction(),
                         ICFactorAction(),
                         DiscriminationAction(),
                         FluxAction())

        return [
            self._make_task_extension([('recall_action', RecallAction, 'MenuBar/File'),
                                       ('batch_edit', BatchEditAction, 'MenuBar/Edit'),
                                       ('reduction_group', reduction_group, 'MenuBar/Data'),
                                       ('figure_group', figure_group, 'MenuBar/Data'),
                                       ('interpreted_age', SetInterpretedAgeAction, 'MenuBar/Data'),

                                       ('equil_inspector', EquilibrationInspectorAction, 'MenuBar/Tools'),
                                       ('data', data_menu, 'MenuBar', {'before': 'Tools', 'after': 'View'}),
                                       ('tag', TagAction, 'MenuBar/Data'),
                                       ('database_save', DatabaseSaveAction, 'MenuBar/Data'),
                                       ('grouping_group', grouping_group, 'MenuBar/Data'),
                                       ('easy_group', lambda: SGroup(id='Easy', name='Easy'), 'MenuBar/Tools'),
                                       ('easy_import', EasyImportAction, 'MenuBar/Tools/Easy'),
                                       ('easy_figures', EasyFiguresAction, 'MenuBar/Tools/Easy'),
                                       ('easy_tables', EasyTablesAction, 'MenuBar/Tools/Easy')]),
            self._make_task_extension([('optimal_equilibration', CalcOptimalEquilibrationAction, 'MenuBar/Tools'),
                                       ('easy_fit', EasyFitAction, 'MenuBar/Tools/Easy')],
                                      task_id='pychron.analysis_edit.isotope_evolution'),
            self._make_task_extension([('easy_blanks', EasyBlanksAction, 'MenuBar/Tools/Easy')],
                                      task_id='pychron.analysis_edit.blanks'),
            self._make_task_extension([('easy_disc', EasyDiscriminationAction, 'MenuBar/Tools/Easy')],
                                      task_id='pychron.analysis_edit.discrimination'),
        ]

    def _meta_task_factory(self, i, f, n, task_group=None,
                           accelerator='', include_view_menu=False):
        return TaskFactory(id=i, factory=f, name=n,
                           task_group=task_group,
                           accelerator=accelerator,
                           include_view_menu=include_view_menu or accelerator
        )

    def _tasks_default(self):
        tasks = [
            ('pychron.recall',
             self._recall_task_factory, 'Recall'),
            ('pychron.advanced_query',
             self._advanced_query_task_factory, 'Advanced Query'),

            ('pychron.analysis_edit.blanks',
             self._blanks_edit_task_factory, 'Blanks'),
            ('pychron.analysis_edit.flux',
             self._flux_task_factory, 'Flux'),
            ('pychron.analysis_edit.isotope_evolution',
             self._iso_evo_task_factory, 'Isotope Evolution'),
            ('pychron.analysis_edit.ic_factor',
             self._ic_factor_task_factory, 'IC Factor'),
            ('pychron.analysis_edit.discrimination',
             self._discrimination_task_factory, 'Discrimination'),

            ('pychron.analysis_edit.batch',
            self._batch_edit_task_factory, 'Batch Edit'),
            #('pychron.analysis_edit.smart_batch',
            # self._smart_batch_edit_task_factory, 'Smart Batch Edit'),

            ('pychron.processing.figures',
             self._figure_task_factory, 'Figures'),
            # ('pychron.processing.publisher', self._publisher_task_factory, 'Publisher'),
            ('pychron.processing.publisher',
             self._table_task_factory, 'Table', '', 'Ctrl+t'),
            ('pychron.processing.respository',
             self._repository_task_factory, 'Repository', '', 'Ctrl+Shift+R'),

        ]

        return [
            self._meta_task_factory(*args)
            for args in tasks
        ]

    def _processor_factory(self):
        return Processor(application=self.application)

    def _blanks_edit_task_factory(self):
        from pychron.processing.tasks.blanks.blanks_task import BlanksTask

        return BlanksTask(manager=self._processor_factory())

    def _flux_task_factory(self):
        from pychron.processing.tasks.flux.flux_task import FluxTask

        return FluxTask(manager=self._processor_factory())

    def _advanced_query_task_factory(self):
        from pychron.processing.tasks.query.advanced_query_task import AdvancedQueryTask

        return AdvancedQueryTask(manager=self._processor_factory())

    def _recall_task_factory(self):
        from pychron.processing.tasks.recall.recall_task import RecallTask

        return RecallTask(manager=self._processor_factory())

    def _iso_evo_task_factory(self):
        from pychron.processing.tasks.isotope_evolution.isotope_evolution_task import IsotopeEvolutionTask

        return IsotopeEvolutionTask(manager=self._processor_factory())

    def _ic_factor_task_factory(self):
        from pychron.processing.tasks.detector_calibration.intercalibration_factor_task import IntercalibrationFactorTask

        return IntercalibrationFactorTask(manager=self._processor_factory())

    def _discrimination_task_factory(self):
        from pychron.processing.tasks.detector_calibration.discrimination_task import DiscrimintationTask

        return DiscrimintationTask(manager=self._processor_factory())

    def _batch_edit_task_factory(self):
        from pychron.processing.tasks.batch_edit.batch_edit_task import BatchEditTask

        return BatchEditTask(manager=self._processor_factory())

    def _smart_batch_edit_task_factory(self):
        from pychron.processing.tasks.batch_edit.smart_batch_edit_task import SmartBatchEditTask

        return SmartBatchEditTask(manager=self._processor_factory())

    def _figure_task_factory(self):
        from pychron.processing.tasks.figures.figure_task import FigureTask

        return FigureTask(manager=self._processor_factory())

    def _repository_task_factory(self):
        from pychron.processing.tasks.repository.respository_task import RepositoryTask

        return RepositoryTask(manager=self._processor_factory())

    def _table_task_factory(self):
        from pychron.processing.tasks.tables.table_task import TableTask

        return TableTask(manager=self._processor_factory())

    def _preferences_panes_default(self):
        return [
            #AutoFigurePreferencesPane,
            ProcessingPreferencesPane]

        #============= EOF =============================================
