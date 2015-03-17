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
from pyface.tasks.action.schema import SMenu, SGroup
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
    ModifyIdentifierAction, CompositeAction, SetSQLiteAction, TimeViewAction, SplitEditorActionHor

from pychron.processing.tasks.actions.edit_actions import BlankEditAction, \
    FluxAction, IsotopeEvolutionAction, ICFactorAction, \
    BatchEditAction, TagAction, DatabaseSaveAction, DiscriminationAction, DataReductionTagAction, \
    SelectDataReductionTagAction
from pychron.processing.tasks.browser.browser_model import BrowserModel
from pychron.processing.tasks.figures.actions import RefreshActiveEditorAction
from pychron.processing.tasks.interpreted_age.actions import OpenInterpretedAgeGroupAction, \
    DeleteInterpretedAgeGroupAction, MakeGroupFromFileAction, MakeDataTablesAction, MakeTASAction
from pychron.processing.tasks.recall.actions import SummaryLabnumberAction, CalculationViewAction
from pychron.processing.tasks.isotope_evolution.actions import CalcOptimalEquilibrationAction
from pychron.processing.tasks.preferences.offline_preferences import OfflinePreferencesPane
from pychron.processing.tasks.preferences.processing_preferences import BrowsingPreferencesPane, EasyPreferencesPane
# from pychron.processing.tasks.browser.browser_task import BrowserTask


def figure_group():
    return SGroup(id='figures.group', name='Figures')


def files_menu():
    return SMenu(id='figure.files.menu', name='From File')


def reduction_group():
    return SGroup(id='reduction.group', name='Reduction')


def data_menu():
    return SMenu(id='data.menu', name='Data')


def grouping_group():
    return SMenu(SGroup(id='grouping'),
                 SGroup(id='graph.grouping'),
                 id='grouping.menu',
                 name='Grouping')


def misc_group():
    return SGroup(id='misc.group')


def analysis_group():
    return SMenu(id='analysis_grouping.menu',
                 name='Analysis Grouping')


# def interpreted_group():
# return SMenu(SetInterpretedAgeAction(),
# OpenInterpretedAgeAction(),
# OpenInterpretedAgeGroupAction(),
# DeleteInterpretedAgeGroupAction(),
#                  MakeGroupFromFileAction(),
#                  name='Interpreted Ages')
#
#
# def analysis_group():
#     return SMenu(MakeAnalysisGroupAction(),
#                  DeleteAnalysisGroupAction(),
#                  name='Analysis Grouping')
#
#
# def recall_group():
#     return Group(RecallAction(),
#                  # OpenAdvancedQueryAction(),
#                  ConfigureRecallAction(),
#                  TimeViewAction())
#
#
#
# def misc_group():
# return Group(TagAction(),
#                  DataReductionTagAction(),
#                  SelectDataReductionTagAction(),
#                  DatabaseSaveAction(),
#                  ClearAnalysisCacheAction(),
#                  MakeTASAction(),
#                  ModifyK3739Action(),
#                  CalculationViewAction(),
#                  SummaryLabnumberAction(),
#                  ModifyIdentifierAction(),
#                  name='misc')

#
# def activate_group():
#     return Group(ActivateBlankAction(),
#         ActivateRecallAction(),
#         ActivateIdeogramAction())


class ProcessingPlugin(BaseTaskPlugin):
    id = 'pychron.processing.plugin'
    name = 'Processing'

    _processor = None

    def set_preference_defaults(self):
        ds = (('recent_hours', 12),)
        self._set_preference_defaults(ds, 'pychron.browsing')

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
            ('pychron.export',
             self._export_task_factory, 'Export'),

            ('pychron.processing.reduction',
             self._reduction_task_factory, 'Reduction'),
            # ('pychron.processing.blanks',
            #  self._blanks_edit_task_factory, 'Blanks'),
            # ('pychron.processing.ic_factor',
            #  self._ic_factor_task_factory, 'IC Factor'),

            ('pychron.processing.flux',
             self._flux_task_factory, 'Flux'),
            ('pychron.processing.isotope_evolution',
             self._iso_evo_task_factory, 'Isotope Evolution'),

            ('pychron.processing.discrimination',
             self._discrimination_task_factory, 'Discrimination'),

            ('pychron.processing.batch',
             self._batch_edit_task_factory, 'Batch Edit'),

            ('pychron.processing.figures',
             self._figure_task_factory, 'Figures'),
            ('pychron.processing.interpreted_age',
             self._interpreted_age_task_factory, 'Interpeted Age'),

            # ('pychron.processing.publisher',
            # self._table_task_factory, 'Table', '', 'Ctrl+t'),
            ('pychron.processing.respository',
             self._repository_task_factory, 'Repository', '', 'Ctrl+Shift+R', '', 'irc-server'),

            # ('pychron.processing.publisher', self._publisher_task_factory, 'Publisher'),
            # ('pychron.processing.vcs',
            #  self._vcs_data_task_factory, 'VCS', '', ''),
            # ('pychron.advanced_query',
            #  self._advanced_query_task_factory, 'Advanced Query'),
            # ('pychron.processing.smart_batch',
            # self._smart_batch_edit_task_factory, 'Smart Batch Edit'),
        ]

        return [self._meta_task_factory(*args) for args in tasks]

    def _processor_factory(self):
        processor = self._processor
        if not processor:
            processor = Processor(application=self.application)
            self._processor = processor
        return processor

    def _export_task_factory(self):
        from pychron.processing.tasks.export.export_task import ExportTask

        return ExportTask(manager=self._processor_factory())

    def _reduction_task_factory(self):
        from pychron.processing.tasks.reduction.reduction_task import ReductionTask
        return ReductionTask(manager=self._processor_factory())
    # def _blanks_edit_task_factory(self):
    #     from pychron.processing.tasks.blanks.blanks_task import BlanksTask
    #
    #     return BlanksTask(manager=self._processor_factory())
    #
    # def _ic_factor_task_factory(self):
    #     from pychron.processing.tasks.detector_calibration.intercalibration_factor_task import \
    #         IntercalibrationFactorTask
    #
    #     return IntercalibrationFactorTask(manager=self._processor_factory())

    def _flux_task_factory(self):
        from pychron.processing.tasks.flux.flux_task import FluxTask

        return FluxTask(manager=self._processor_factory())

    def _recall_task_factory(self):
        from pychron.processing.tasks.recall.recall_task import RecallTask

        return RecallTask(manager=self._processor_factory())

    def _iso_evo_task_factory(self):
        from pychron.processing.tasks.isotope_evolution.isotope_evolution_task import IsotopeEvolutionTask

        return IsotopeEvolutionTask(manager=self._processor_factory())


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

    # def _table_task_factory(self):
    # from pychron.processing.tasks.tables.table_task import TableTask
    #
    #     return TableTask(manager=self._processor_factory())

    def _interpreted_age_task_factory(self):
        from pychron.processing.tasks.interpreted_age.interpreted_age_task import InterpretedAgeTask

        return InterpretedAgeTask(manager=self._processor_factory())

    def _browser_model_factory(self):
        return BrowserModel(manager=self._processor_factory())

    # defaults
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=BrowserModel,
                                        factory=self._browser_model_factory)
        so1 = self.service_offer_factory(protocol=Processor,
                                         factory=self._processor_factory)
        return [so, so1]

    def _preferences_panes_default(self):
        return [
            BrowsingPreferencesPane,
            # VCSPreferencesPane,
            OfflinePreferencesPane, EasyPreferencesPane]

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
                ('pychron.refresh_plot', 'Ctrl+Shift+R', 'Refresh Plot'),
                ('pychron.recall', 'Ctrl+R', 'Open Recall')]

    def _file_defaults_default(self):
        return [('ideogram_defaults', 'IDEOGRAM_DEFAULTS', True),
                ('spectrum_defaults', 'SPECTRUM_DEFAULTS', True),
                ('inverse_isochron_defaults', 'INVERSE_ISOCHRON_DEFAULTS', True),
                ('composites_defaults', 'COMPOSITE_DEFAULTS', True),
                ('screen_formatting_options', 'SCREEN_FORMATTING_DEFAULTS', True),
                ('presentation_formatting_options', 'PRESENTATION_FORMATTING_DEFAULTS', True),
                ('display_formatting_options', 'DISPLAY_FORMATTING_DEFAULTS', True)]

    def _help_tips_default(self):
        return ['Use <b>Data>Ideogram</b> to plot an Ideogram',
                'Use <b>Data>Spectrum</b> to plot a Spectrum',
                'Use <b>Data>Recall</b> or <b>File/Recall</b> to view analytical data for individual analyses']

    def _task_extensions_default(self):
        extensions = [TaskExtension(actions=actions, task_id=eid) for eid, actions in self._get_extensions()]

        additions = [SchemaAddition(id='data',
                                    before='tools.menu',
                                    after='view.menu',
                                    factory=data_menu,
                                    path='MenuBar')]
        aflag = False
        ffflag = False
        fflag = False
        mflag = False
        gflag = False
        rflag = False
        for eid, actions in self._get_extensions():
            for ai in actions:
                if not aflag and ai.id.startswith('pychron.agroup'):
                    aflag = True
                    additions.append(SchemaAddition(id='analysis_grouping_menu',
                                                    factory=analysis_group,
                                                    path='MenuBar/data.menu'), )
                elif not ffflag and ai.id.startswith('pychron.figure.file'):
                    ffflag = True
                    additions.append(SchemaAddition(id='file_menu',
                                                    factory=files_menu,
                                                    path='MenuBar/data.menu/figures.group'))

                elif not fflag and ai.id.startswith('pychron.figure'):
                    fflag = True
                    additions.append(SchemaAddition(id='figure_group',
                                                    factory=figure_group,
                                                    path='MenuBar/data.menu'))
                elif not gflag and ai.id.startswith('pychron.grouping'):
                    gflag = True
                    additions.append(SchemaAddition(id='grouping_group',
                                                    factory=grouping_group,
                                                    before='reduction_group',
                                                    path='MenuBar/data.menu'))
                elif not mflag and ai.id.startswith('pychron.misc'):
                    mflag = True
                    additions.append(SchemaAddition(id='misc_Group',
                                                    factory=misc_group,
                                                    path='MenuBar/data.menu'))
                elif not rflag and ai.id.startswith('pychron.reduction'):
                    rflag = True
                    additions.append(SchemaAddition(id='reduction_group',
                                                    factory=reduction_group,
                                                    path='MenuBar/data.menu'))

        extensions.append(TaskExtension(actions=additions))
        return extensions

    def _available_task_extensions_default(self):
        # ('recall_action', RecallAction, 'MenuBar/file.menu'),
        #                ('recall_group', recall_group, 'MenuBar/data.menu', {'absolute_position': 'first'}),
        #                ('data', data_menu, 'MenuBar', {'before': 'tools.menu', 'after': 'view.menu'}),
        #                ('activate_group', activate_group, 'MenuBar/view.menu'),
        #                ('reduction_group', reduction_group, 'MenuBar/data.menu'),
        #                ('figure_group', figure_group, 'MenuBar/data.menu')
        fgpath = 'MenuBar/data.menu/figures.group'
        rgpath = 'MenuBar/data.menu/reduction.group'
        mpath = 'MenuBar/data.menu/misc.group'
        ggpath = 'MenuBar/data.menu/grouping.menu/grouping'
        gggpath = 'MenuBar/data.menu/grouping.menu/graph.grouping'
        ffpath = 'MenuBar/data.menu/figures.group/figure.files.menu'
        apath = 'MenuBar/data.menu/analysis_grouping.menu'
        return [('{}.figures'.format(self.id), '', 'Figures',
                 [SchemaAddition(id='pychron.figure.spectrum', factory=SpectrumAction, path=fgpath),
                  SchemaAddition(id='pychron.figure.ideogram', factory=IdeogramAction, path=fgpath),
                  SchemaAddition(id='pychron.figure.inv_isochron', factory=InverseIsochronAction, path=fgpath),
                  SchemaAddition(id='pychron.figure.series', factory=SeriesAction, path=fgpath),
                  SchemaAddition(id='pychron.figure.composite', factory=CompositeAction, path=fgpath),
                  SchemaAddition(id='pychron.figure.xyscatter', factory=XYScatterAction, path=fgpath),
                  SchemaAddition(id='pychron.figure.file_ideogram', factory=IdeogramFromFile, path=ffpath),
                  SchemaAddition(id='pychron.figure.file_spectrum', factory=SpectrumFromFile, path=ffpath),
                  SchemaAddition(id='pychron.figure.refresh', factory=RefreshActiveEditorAction, path=fgpath)]),

                 ('{}.agroup'.format(self.id), '', 'Analysis Grouping',
                  [SchemaAddition(id='pychron.agroup.make', factory=MakeAnalysisGroupAction, path=apath),
                   SchemaAddition(id='pychron.agroup.delete', factory=DeleteAnalysisGroupAction, path=apath)]),
                 ('{}.grouping'.format(self.id), '', 'Grouping',
                  [SchemaAddition(id='pychron.grouping.selected', factory=GroupSelectedAction, path=ggpath),
                   SchemaAddition(id='pychron.grouping.aliquot', factory=GroupbyAliquotAction, path=ggpath),
                   SchemaAddition(id='pychron.grouping.lnumber', factory=GroupbyLabnumberAction, path=ggpath),
                   SchemaAddition(id='pychron.grouping.sample', factory=GroupbySampleAction, path=ggpath),
                   SchemaAddition(id='pychron.grouping.clear', factory=ClearGroupAction, path=ggpath),

                   SchemaAddition(id='pychron.grouping.gselected', factory=GraphGroupSelectedAction, path=gggpath),
                   SchemaAddition(id='pychron.grouping.gsample', factory=GraphGroupbySampleAction, path=gggpath)]),

                 ('{}.misc'.format(self.id), '', 'Misc',
                  [SchemaAddition(id='pychron.misc.tag', factory=TagAction, path=mpath),
                   SchemaAddition(id='pychron.misc.drtag', factory=DataReductionTagAction, path=mpath),
                   SchemaAddition(id='pychron.misc.select_drtag', factory=SelectDataReductionTagAction, path=mpath),
                   SchemaAddition(id='pychron.misc.db_save', factory=DatabaseSaveAction, path=mpath),
                   SchemaAddition(id='pychron.misc.clear_cache', factory=ClearAnalysisCacheAction, path=mpath),
                   # SchemaAddition(id='pychron.misc', factory=MakeTASAction, path=mpath),
                   SchemaAddition(id='pychron.misc.modify_k', factory=ModifyK3739Action, path=mpath),
                   # SchemaAddition(id='pychron.misc', factory=CalculationViewAction, path=mpath),
                   # SchemaAddition(id='pychron.misc', factory=SummaryLabnumberAction, path=mpath),
                   SchemaAddition(id='pychron.misc.modify_identifier', factory=ModifyIdentifierAction, path=mpath)]),

                 ('{}.reduction'.format(self.id), '', 'Reduction',
                  [SchemaAddition(id='pychron.reduction.iso_evo', factory=IsotopeEvolutionAction, path=rgpath),
                   SchemaAddition(id='pychron.reduction.blanks', factory=BlankEditAction, path=rgpath),
                   SchemaAddition(id='pychron.reduction.ic_factor', factory=ICFactorAction, path=rgpath),
                   SchemaAddition(id='pychron.reduction.discrimination', factory=DiscriminationAction, path=rgpath),
                   SchemaAddition(id='pychron.reduction.flux', factory=FluxAction, path=rgpath), ])]

        # ============= EOF =============================================

        # def _dataset_factory(self):
        #     return DataSetTask(manager=self._prcoessor_factory())

        # def _vcs_data_task_factory(self):
        #     from pychron.processing.tasks.vcs_data.vcs_data_task import VCSDataTask
        #     return VCSDataTask(manager=self._processor_factory())

        # def _advanced_query_task_factory(self):
        #     from pychron.processing.tasks.query.advanced_query_task import AdvancedQueryTask
        #
        #     return AdvancedQueryTask(manager=self._processor_factory())

        # def _make_task_extension(self, actions, **kw):
        #     def make_schema(args):
        #         if len(args) == 3:
        #             mkw = {}
        #             i, f, p = args
        #         else:
        #             i, f, p, mkw = args
        #         return SchemaAddition(id=i, factory=f, path=p, **mkw)
        #
        #     return TaskExtension(actions=[make_schema(args)
        #                                   for args in actions], **kw)
        #
        # def _simple_ui_task_extensions(self):
        # actions = [('recall_action', RecallAction, 'MenuBar/file.menu'),
        #                ('recall_group', recall_group, 'MenuBar/data.menu', {'absolute_position': 'first'}),
        #                ('data', data_menu, 'MenuBar', {'before': 'tools.menu', 'after': 'view.menu'}),
        #                ('activate_group', activate_group, 'MenuBar/view.menu'),
        #                ('reduction_group', reduction_group, 'MenuBar/data.menu'),
        #                ('figure_group', figure_group, 'MenuBar/data.menu')]
        #     exts = [self._make_task_extension(actions)]
        #     return exts
        #
        # def _advanced_ui_task_extensions(self):
        #     actions = [('recall_action', RecallAction, 'MenuBar/file.menu'),
        #                # ('find_action', OpenAdvancedQueryAction, 'MenuBar/file.menu'),
        #                ('export_analyses', ExportAnalysesAction, 'MenuBar/file.menu'),
        #                ('set_sqlite_dataset', SetSQLiteAction, 'MenuBar/file.menu'),
        #
        #                ('batch_edit', BatchEditAction, 'MenuBar/Edit'),
        #
        #                ('recall_group', recall_group, 'MenuBar/data.menu', {'absolute_position': 'first'}),
        #                ('data', data_menu, 'MenuBar', {'before': 'tools.menu', 'after': 'view.menu'}),
        #
        #
        #                ('activate_group', activate_group, 'MenuBar/view.menu'),
        #                ('reduction_group', reduction_group, 'MenuBar/data.menu'),
        #                ('figure_group', figure_group, 'MenuBar/data.menu'),
        #                ('interpreted_group', interpreted_group, 'MenuBar/data.menu'),
        #                ('grouping_group', grouping_group, 'MenuBar/data.menu'),
        #
        #                ('misc_group', misc_group, 'MenuBar/data.menu'),
        #                # ('tag', TagAction, 'MenuBar/data.menu'),
        #                # ('database_save', DatabaseSaveAction, 'MenuBar/data.menu'),
        #
        #                # ('graph_grouping_group', graph_grouping_group, 'MenuBar/data.menu'),
        #                # ('clear_cache', ClearAnalysisCacheAction, 'MenuBar/data.menu'),
        #                ('make_analysis_group', analysis_group, 'MenuBar/data.menu'),
        #                ('make_data_tables', MakeDataTablesAction, 'MenuBar/data.menu',
        #                 {'absolute_position': 'last'}),
        #                # ('make_tas', MakeTASAction, 'MenuBar/data.menu'),
        #                # ('modify_k3739', ModifyK3739Action, 'MenuBar/data.menu'),
        #
        #                ('equil_inspector', EquilibrationInspectorAction, 'MenuBar/tools.menu'),
        #                ('split_editor_area', SplitEditorActionHor, 'MenuBar/window.menu'),
        #                ('split_editor_area', SplitEditorActionVert, 'MenuBar/window.menu')]
        #
        #     exts = [self._make_task_extension(actions)]
        #
        #     # use_vcs = to_bool(self.application.preferences.get('pychron.vcs.use_vcs'))
        #     # if use_vcs:
        #     # exts.append(self._make_task_extension([('vcs', vcs_menu, 'MenuBar', {'after': 'view.menu'}),
        #     #                                            ('vcs_pull', PullVCSAction, 'MenuBar/vcs.menu'),
        #     #                                            ('vcs_push', PushVCSAction, 'MenuBar/vcs.menu')]))
        #
        #     use_easy = to_bool(self.application.preferences.get('pychron.processing.use_easy'))
        #     if use_easy:
        #         def easy_group():
        #             return Group(EasyImportAction(),
        #                          EasyFiguresAction(),
        #                          EasyCompareAction(),
        #                          EasyTablesAction(),
        #                          EasySensitivityAction(),
        #                          EasyFaradayICAction(),
        #                          EasyAverageBlanksAction(),
        #                          id='easy.group')
        #
        #         grp = self._make_task_extension([('easy_group', easy_group, 'MenuBar/tools.menu')])
        #         a = self._make_task_extension(
        #             [('optimal_equilibration', CalcOptimalEquilibrationAction, 'MenuBar/tools.menu'),
        #              ('easy_fit', EasyFitAction, 'MenuBar/tools.menu')],
        #             task_id='pychron.processing.isotope_evolution')
        #
        #         b = self._make_task_extension([('easy_blanks', EasyBlanksAction, 'MenuBar/tools.menu')],
        #                                       task_id='pychron.processing.blanks')
        #
        #         c = self._make_task_extension([('easy_disc', EasyDiscriminationAction, 'MenuBar/tools.menu')],
        #                                       task_id='pychron.processing.discrimination')
        #
        #         d = self._make_task_extension([('easy_ic', EasyICAction, 'MenuBar/tools.menu')],
        #                                       task_id='pychron.processing.ic_factor')
        #
        #         e = self._make_task_extension([('easy_flux', EasyFluxAction, 'MenuBar/tools.menu')],
        #                                       task_id='pychron.processing.flux')
        #
        #         exts.extend((grp, a, b, c, d, e))
        #
        #     return exts