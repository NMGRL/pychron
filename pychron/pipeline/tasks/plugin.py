# ===============================================================================
# Copyright 2015 Jake Ross
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
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu, SGroup
from pyface.tasks.action.schema_addition import SchemaAddition

from pychron.envisage.browser.interpreted_age_browser_model import InterpretedAgeBrowserModel
from pychron.envisage.browser.sample_browser_model import SampleBrowserModel
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.paths import paths
from pychron.pipeline.tasks.actions import ConfigureRecallAction, IdeogramAction, SpectrumAction, \
    SeriesAction, BlanksAction, ICFactorAction, ResetFactoryDefaultsAction, LastNAnalysesSeriesAction, \
    LastNHoursSeriesAction, LastMonthSeriesAction, LastWeekSeriesAction, LastDaySeriesAction, FluxAction, \
    FreezeProductionRatios, InverseIsochronAction, IsoEvolutionAction, ExtractionAction, RecallAction, \
    AnalysisTableAction, ClearAnalysisSetsAction
from pychron.pipeline.tasks.preferences import PipelinePreferencesPane
from pychron.pipeline.tasks.task import PipelineTask


class PipelinePlugin(BaseTaskPlugin):
    def _file_defaults_default(self):
        ov = True
        files = [['pipeline_template_file', 'PIPELINE_TEMPLATES', ov],
                 ['icfactor_template', 'ICFACTOR', ov],
                 ['blanks_template', 'BLANKS', ov],
                 ['iso_evo_template', 'ISOEVO', ov],
                 ['ideogram_template', 'IDEO', ov],
                 ['spectrum_template', 'SPEC', ov],
                 ['series_template', 'SERIES', ov],
                 ['inverse_isochron_template', 'INVERSE_ISOCHRON', ov],
                 ['csv_ideogram_template', 'CSV_IDEO', ov],
                 ['flux_template', 'FLUX', ov],
                 ['vertical_flux_template', 'VERTICAL_FLUX', ov],
                 ['xy_scatter_template', 'XY_SCATTER', ov],
                 ['analysis_table_template', 'ANALYSIS_TABLE', ov],
                 ['interpreted_age_ideogram_template', 'INTERPRETED_AGE_IDEOGRAM', ov],
                 ['interpreted_age_table_template', 'INTERPRETED_AGE_TABLE', ov],
                 ['auto_ideogram_template', 'AUTO_IDEOGRAM', ov],
                 ['geochron_template', 'GEOCHRON', ov],
                 ['yield_template', 'YIELD', ov],
                 ['csv_analyses_export_template', 'CSV_ANALYSES_EXPORT', ov]]

        files = paths.set_template_manifest(files)
        return files

    def _pipeline_factory(self):
        model = self.application.get_service(SampleBrowserModel)
        iamodel = self.application.get_service(InterpretedAgeBrowserModel)
        t = PipelineTask(browser_model=model,
                         interpreted_age_browser_model=iamodel,
                         application=self.application)
        return t

    # def _browser_factory(self):
    #     model = self.application.get_service(SampleBrowserModel)
    #     t = BrowserTask(browser_model=model,
    #                     application=self.application)
    #     return t

    def _browser_model_factory(self):
        return SampleBrowserModel(application=self.application)

    def _interpreted_age_browser_model_factory(self):
        return InterpretedAgeBrowserModel(application=self.application)

    # defaults
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=SampleBrowserModel,
                                        factory=self._browser_model_factory)

        so1 = self.service_offer_factory(protocol=InterpretedAgeBrowserModel,
                                         factory=self._interpreted_age_browser_model_factory)
        return [so, so1]

    def _preferences_panes_default(self):
        return [PipelinePreferencesPane]

    def _task_extensions_default(self):
        def data_menu():
            return SMenu(id='data.menu', name='Data')

        def plot_group():
            return SGroup(id='plot.group')

        def reduction_group():
            return SGroup(id='reduction.group')

        def quick_series_group():
            return SGroup(id='quick_series.group')

        def recall_group():
            return SGroup(id='recall.group')

        pg = 'MenuBar/data.menu/plot.group'
        rg = 'MenuBar/data.menu/reduction.group'
        reg = 'MenuBar/data.menu/recall.group'
        qsg = 'MenuBar/data.menu/quick_series.group'

        recall_actions = [SchemaAddition(factory=recall_group,
                                         path='MenuBar/data.menu'),
                          SchemaAddition(factory=RecallAction,
                                         path=reg),
                          # SchemaAddition(factory=TimeViewBrowserAction,
                          #                path=reg)
                          ]

        plotting_actions = [SchemaAddition(factory=data_menu,
                                           path='MenuBar',
                                           before='tools.menu',
                                           after='view.menu', ),
                            SchemaAddition(factory=plot_group,
                                           path='MenuBar/data.menu'),
                            SchemaAddition(factory=IdeogramAction,
                                           path=pg),
                            SchemaAddition(factory=SpectrumAction,
                                           path=pg),
                            # SchemaAddition(factory=IsochronAction,
                            #                path=pg),
                            SchemaAddition(factory=InverseIsochronAction,
                                           path=pg),
                            SchemaAddition(factory=SeriesAction,
                                           path=pg),
                            # SchemaAddition(factory=VerticalFluxAction,
                            #                path=pg),
                            SchemaAddition(factory=ExtractionAction,
                                           path=pg)]

        reduction_actions = [SchemaAddition(factory=reduction_group,
                                            path='MenuBar/data.menu'),
                             SchemaAddition(factory=IsoEvolutionAction,
                                            path=rg),
                             SchemaAddition(factory=BlanksAction,
                                            path=rg),
                             SchemaAddition(factory=ICFactorAction,
                                            path=rg),
                             SchemaAddition(factory=FluxAction,
                                            path=rg),
                             SchemaAddition(factory=AnalysisTableAction,
                                            path=rg),
                             SchemaAddition(factory=FreezeProductionRatios,
                                            path=rg)]

        help_actions = [SchemaAddition(factory=ResetFactoryDefaultsAction,
                                       path='MenuBar/help.menu'),
                        SchemaAddition(factory=ClearAnalysisSetsAction,
                                       path='MenuBar/help.menu')]
        configure_recall = SchemaAddition(factory=ConfigureRecallAction,
                                          path='MenuBar/Edit')
        # browser_actions = [configure_recall]

        quick_series_actions = [SchemaAddition(factory=quick_series_group,
                                               path='MenuBar/data.menu'),
                                SchemaAddition(factory=LastNAnalysesSeriesAction,
                                               path=qsg),
                                SchemaAddition(factory=LastNHoursSeriesAction,
                                               path=qsg),
                                SchemaAddition(factory=LastDaySeriesAction,
                                               path=qsg),
                                SchemaAddition(factory=LastWeekSeriesAction,
                                               path=qsg),
                                SchemaAddition(factory=LastMonthSeriesAction,
                                               path=qsg), ]

        actions = recall_actions
        actions.extend(plotting_actions)
        actions.extend(reduction_actions)
        actions.extend(help_actions)
        actions.extend(quick_series_actions)

        return [TaskExtension(task_id='pychron.pipeline.task',
                              actions=[configure_recall]),
                # TaskExtension(task_id='pychron.browser.task',
                #               actions=browser_actions),
                TaskExtension(actions=actions)]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.pipeline.task',
                            name='Pipeline',
                            accelerator='Ctrl+p',
                            factory=self._pipeline_factory),
                # TaskFactory(id='pychron.browser.task',
                #             name='Browser',
                #             accelerator='Ctrl+b',
                #             factory=self._browser_factory)
                ]

# ============= EOF =============================================
