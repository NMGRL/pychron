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
# ===============================================================================

# ============= enthought library imports =======================
from envisage.ui.tasks.task_factory import TaskFactory
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.action.menu_manager import MenuManager
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.action.group import Group
from pyface.tasks.action.schema import SMenu
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import to_bool

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.processing.processor import Processor
from pychron.processing.tasks.actions.import_actions import EasyImportAction
from pychron.processing.tasks.actions.easy_actions import EasyFitAction, EasyBlanksAction, EasyDiscriminationAction, \
    EasyFiguresAction, EasyTablesAction, EasyICAction, EasyFluxAction, EasySensitivityAction, EasyCompareAction, \
    EasyFaradayICAction, EasyAverageBlanksAction
from pychron.processing.tasks.actions.processing_actions import IdeogramAction, \
    RecallAction, SpectrumAction, \
    EquilibrationInspectorAction, InverseIsochronAction, GroupSelectedAction, \
    GroupbyAliquotAction, GroupbyLabnumberAction, ClearGroupAction, \
    SeriesAction, SetInterpretedAgeAction, OpenInterpretedAgeAction, ClearAnalysisCacheAction, \
    ExportAnalysesAction, \
    GraphGroupSelectedAction, IdeogramFromFile, SpectrumFromFile, MakeAnalysisGroupAction, GraphGroupbySampleAction, \
    DeleteAnalysisGroupAction, XYScatterAction, ModifyK3739Action, GroupbySampleAction, \
    SplitEditorActionVert, ConfigureRecallAction, ActivateBlankAction, ActivateRecallAction, ActivateIdeogramAction, \
    ModifyIdentifierAction

from pychron.processing.tasks.actions.edit_actions import BlankEditAction, \
    FluxAction, IsotopeEvolutionAction, ICFactorAction, \
    BatchEditAction, TagAction, DatabaseSaveAction, DiscriminationAction, DataReductionTagAction, \
    SelectDataReductionTagAction
from pychron.processing.tasks.figures.actions import RefreshActiveEditorAction
from pychron.processing.tasks.interpreted_age.actions import OpenInterpretedAgeGroupAction, \
    DeleteInterpretedAgeGroupAction, MakeGroupFromFileAction, MakeDataTablesAction, MakeTASAction
from pychron.processing.tasks.recall.actions import SummaryLabnumberAction, CalculationViewAction
from pychron.processing.tasks.isotope_evolution.actions import CalcOptimalEquilibrationAction
from pychron.processing.tasks.preferences.offline_preferences import OfflinePreferencesPane
from pychron.processing.tasks.preferences.processing_preferences import BrowsingPreferencesPane, EasyPreferencesPane
#from pychron.processing.tasks.browser.browser_task import BrowserTask
from pyface.message_dialog import warning


class ProcessingPlugin(BaseTaskPlugin):
    id = 'pychron.processing.plugin'
    name = 'Processing'

    def set_preference_defaults(self):
        ds = (('recent_hours',12),)
        self._set_preference_defaults(ds, 'pychron.browsing')

    def _actions_default(self):
        return [('pychron.ideogram', 'Ctrl+J', 'Open Ideogram'),
                ('pychron.spectrum', 'Ctrl+D', 'Open Spectrum'),
                ('pychron.series', 'Ctrl+U', 'Open Series'),
                ('pychron.inverse_isochron', 'Ctrl+I', 'Open Inverse Isochron'),
                ('pychron.tag', 'Ctrl+Shift+T', 'Tag'),
                ('pychron.flux', 'Ctrl+G', 'Flux'),
                ('pychron.blank', 'Ctrl+B', 'Blanks'),
                ('pychron.isotope_evolution', 'Ctrl+K', 'Isotope Evolutions'),
                ('pychron.ic_factor', 'Ctrl+Shift+I', 'IC Factors'),
                ('pychron.refresh_plot','Ctrl+Shift+R','Refresh Plot'),
                ('pychron.recall', 'Ctrl+R', 'Open Recall')]

    def _service_offers_default(self):
        process_so = self.service_offer_factory(
            protocol=Processor,
            factory=self._processor_factory)

        return [process_so]

    # def start(self):
#         try:
#             import xlwt
#         except ImportError:
#             warning(None, '''"xlwt" package not installed.
#
# Install to enable MS Excel export''')
#         super

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
                XYScatterAction(),
                MenuManager(IdeogramFromFile(),
                            SpectrumFromFile(),
                            name='From File'),
                RefreshActiveEditorAction(),
                name='Figures')

        def data_menu():
            return SMenu(id='data.menu', name='Data')

        # def vcs_menu():
        #     return SMenu(id='vcs.menu', name='VCS')

        def grouping_group():
            return SMenu(Group(GroupSelectedAction(),
                               GroupbyAliquotAction(),
                               GroupbyLabnumberAction(),
                               GroupbySampleAction(),
                               ClearGroupAction()),
                         Group(GraphGroupSelectedAction(),
                               GraphGroupbySampleAction()),
                         name='Grouping')

        def reduction_group():
            return Group(IsotopeEvolutionAction(),
                         BlankEditAction(),
                         ICFactorAction(),
                         DiscriminationAction(),
                         FluxAction(),
                         name='Reduction')

        def interpreted_group():
            return SMenu(SetInterpretedAgeAction(),
                         OpenInterpretedAgeAction(),
                         OpenInterpretedAgeGroupAction(),
                         DeleteInterpretedAgeGroupAction(),
                         MakeGroupFromFileAction(),
                         name='Interpreted Ages')

        def analysis_group():
            return SMenu(MakeAnalysisGroupAction(),
                         DeleteAnalysisGroupAction(),
                         name='Analysis Grouping')

        def recall_group():
            return Group(RecallAction(),
                         # OpenAdvancedQueryAction(),
                         ConfigureRecallAction())

        def misc_group():
            return Group(TagAction(),
                         DataReductionTagAction(),
                         SelectDataReductionTagAction(),
                         DatabaseSaveAction(),
                         ClearAnalysisCacheAction(),
                         MakeTASAction(),
                         ModifyK3739Action(),
                         CalculationViewAction(),
                         SummaryLabnumberAction(),
                         ModifyIdentifierAction(),
                         name='misc')

        def activate_group():
            return Group(ActivateBlankAction(),
                         ActivateRecallAction(),
                         ActivateIdeogramAction())

        default_actions = [('recall_action', RecallAction, 'MenuBar/file.menu'),
                           #('find_action', OpenAdvancedQueryAction, 'MenuBar/file.menu'),
                           ('export_analyses', ExportAnalysesAction, 'MenuBar/file.menu'),

                           ('batch_edit', BatchEditAction, 'MenuBar/Edit'),

                           ('recall_group', recall_group, 'MenuBar/data.menu', {'absolute_position': 'first'}),
                           ('data', data_menu, 'MenuBar', {'before': 'tools.menu', 'after': 'view.menu'}),


                           ('activate_group', activate_group, 'MenuBar/view.menu'),
                           ('reduction_group', reduction_group, 'MenuBar/data.menu'),
                           ('figure_group', figure_group, 'MenuBar/data.menu'),
                           ('interpreted_group', interpreted_group, 'MenuBar/data.menu'),
                           ('grouping_group', grouping_group, 'MenuBar/data.menu'),

                           ('misc_group', misc_group, 'MenuBar/data.menu'),
                           # ('tag', TagAction, 'MenuBar/data.menu'),
                           # ('database_save', DatabaseSaveAction, 'MenuBar/data.menu'),

                           # ('graph_grouping_group', graph_grouping_group, 'MenuBar/data.menu'),
                           # ('clear_cache', ClearAnalysisCacheAction, 'MenuBar/data.menu'),
                           ('make_analysis_group', analysis_group, 'MenuBar/data.menu'),
                           ('make_data_tables', MakeDataTablesAction, 'MenuBar/data.menu',
                            {'absolute_position': 'last'}),
                           # ('make_tas', MakeTASAction, 'MenuBar/data.menu'),
                           # ('modify_k3739', ModifyK3739Action, 'MenuBar/data.menu'),

                           ('equil_inspector', EquilibrationInspectorAction, 'MenuBar/tools.menu'),
                           # ('split_editor_area', SplitEditorActionHor, 'MenuBar/window.menu'),
                           ('split_editor_area', SplitEditorActionVert, 'MenuBar/window.menu')]

        exts = [self._make_task_extension(default_actions)]

        # use_vcs = to_bool(self.application.preferences.get('pychron.vcs.use_vcs'))
        # if use_vcs:
        #     exts.append(self._make_task_extension([('vcs', vcs_menu, 'MenuBar', {'after': 'view.menu'}),
        #                                            ('vcs_pull', PullVCSAction, 'MenuBar/vcs.menu'),
        #                                            ('vcs_push', PushVCSAction, 'MenuBar/vcs.menu')]))

        use_easy = to_bool(self.application.preferences.get('pychron.processing.use_easy'))
        if use_easy:
            def easy_group():
                return Group(EasyImportAction(),
                             EasyFiguresAction(),
                             EasyCompareAction(),
                             EasyTablesAction(),
                             EasySensitivityAction(),
                             EasyFaradayICAction(),
                             EasyAverageBlanksAction(),
                             id='easy.group')

            grp = self._make_task_extension([('easy_group', easy_group, 'MenuBar/tools.menu')])
            a = self._make_task_extension(
                [('optimal_equilibration', CalcOptimalEquilibrationAction, 'MenuBar/tools.menu'),
                 ('easy_fit', EasyFitAction, 'MenuBar/tools.menu')],
                task_id='pychron.processing.isotope_evolution')

            b = self._make_task_extension([('easy_blanks', EasyBlanksAction, 'MenuBar/tools.menu')],
                                          task_id='pychron.processing.blanks')

            c = self._make_task_extension([('easy_disc', EasyDiscriminationAction, 'MenuBar/tools.menu')],
                                          task_id='pychron.processing.discrimination')

            d = self._make_task_extension([('easy_ic', EasyICAction, 'MenuBar/tools.menu')],
                                          task_id='pychron.processing.ic_factor')

            e = self._make_task_extension([('easy_flux', EasyFluxAction, 'MenuBar/tools.menu')],
                                          task_id='pychron.processing.flux')

            exts.extend((grp, a, b, c, d, e))

        return exts

    def _meta_task_factory(self, i, f, n, task_group=None,
                           accelerator='', include_view_menu=False,
                           image=None):
        return TaskFactory(id=i, factory=f, name=n,
                           task_group=task_group,
                           accelerator=accelerator,
                           image=image,
                           include_view_menu=include_view_menu or accelerator)

    def _tasks_default(self):
        tasks = [
            ('pychron.recall',
             self._recall_task_factory, 'Recall'),
            # ('pychron.advanced_query',
            #  self._advanced_query_task_factory, 'Advanced Query'),

            ('pychron.processing.blanks',
             self._blanks_edit_task_factory, 'Blanks'),
            ('pychron.processing.flux',
             self._flux_task_factory, 'Flux'),
            ('pychron.processing.isotope_evolution',
             self._iso_evo_task_factory, 'Isotope Evolution'),
            ('pychron.processing.ic_factor',
             self._ic_factor_task_factory, 'IC Factor'),
            ('pychron.processing.discrimination',
             self._discrimination_task_factory, 'Discrimination'),

            ('pychron.processing.batch',
             self._batch_edit_task_factory, 'Batch Edit'),
            #('pychron.processing.smart_batch',
            # self._smart_batch_edit_task_factory, 'Smart Batch Edit'),

            ('pychron.processing.figures',
             self._figure_task_factory, 'Figures'),
            ('pychron.processing.interpreted_age',
             self._interpreted_age_task_factory, 'Interpeted Age'),

            # ('pychron.processing.publisher', self._publisher_task_factory, 'Publisher'),
            ('pychron.processing.publisher',
             self._table_task_factory, 'Table', '', 'Ctrl+t'),
            ('pychron.processing.respository',
             self._repository_task_factory, 'Repository', '', 'Ctrl+Shift+R', '', 'irc-server'),
            # ('pychron.processing.vcs',
            #  self._vcs_data_task_factory, 'VCS', '', ''),
            ]

        return [self._meta_task_factory(*args) for args in tasks]

    def _processor_factory(self):
        return Processor(application=self.application)

    # def _dataset_factory(self):
    #     return DataSetTask(manager=self._prcoessor_factory())

    def _blanks_edit_task_factory(self):
        from pychron.processing.tasks.blanks.blanks_task import BlanksTask

        return BlanksTask(manager=self._processor_factory())

    def _flux_task_factory(self):
        from pychron.processing.tasks.flux.flux_task import FluxTask

        return FluxTask(manager=self._processor_factory())

    # def _advanced_query_task_factory(self):
    #     from pychron.processing.tasks.query.advanced_query_task import AdvancedQueryTask
    #
    #     return AdvancedQueryTask(manager=self._processor_factory())

    def _recall_task_factory(self):
        from pychron.processing.tasks.recall.recall_task import RecallTask

        return RecallTask(manager=self._processor_factory())

    def _iso_evo_task_factory(self):
        from pychron.processing.tasks.isotope_evolution.isotope_evolution_task import IsotopeEvolutionTask

        return IsotopeEvolutionTask(manager=self._processor_factory())

    def _ic_factor_task_factory(self):
        from pychron.processing.tasks.detector_calibration.intercalibration_factor_task import \
            IntercalibrationFactorTask

        return IntercalibrationFactorTask(manager=self._processor_factory())

    def _discrimination_task_factory(self):
        from pychron.processing.tasks.detector_calibration.discrimination_task import DiscrimintationTask

        return DiscrimintationTask(manager=self._processor_factory())

    def _batch_edit_task_factory(self):
        from pychron.processing.tasks.batch_edit.batch_edit_task import BatchEditTask

        return BatchEditTask(manager=self._processor_factory())

    def _figure_task_factory(self):
        from pychron.processing.tasks.figures.figure_task import FigureTask

        return FigureTask(manager=self._processor_factory())

    def _repository_task_factory(self):
        from pychron.processing.tasks.repository.respository_task import RepositoryTask

        return RepositoryTask(manager=self._processor_factory())

    def _table_task_factory(self):
        from pychron.processing.tasks.tables.table_task import TableTask

        return TableTask(manager=self._processor_factory())

    def _interpreted_age_task_factory(self):
        from pychron.processing.tasks.interpreted_age.interpreted_age_task import InterpretedAgeTask

        return InterpretedAgeTask(manager=self._processor_factory())

    # def _vcs_data_task_factory(self):
    #     from pychron.processing.tasks.vcs_data.vcs_data_task import VCSDataTask
    #     return VCSDataTask(manager=self._processor_factory())

    def _preferences_panes_default(self):
        return [
            BrowsingPreferencesPane,
            # VCSPreferencesPane,
            OfflinePreferencesPane, EasyPreferencesPane]
# ============= EOF =============================================
