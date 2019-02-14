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

from envisage.extension_point import ExtensionPoint
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu, SGroup
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import List

from pychron.dvc.dvc import DVC
from pychron.envisage.browser.interpreted_age_browser_model import InterpretedAgeBrowserModel
from pychron.envisage.browser.sample_browser_model import SampleBrowserModel
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.pipeline.tasks.actions import ConfigureRecallAction, IdeogramAction, SpectrumAction, \
    SeriesAction, BlanksAction, ICFactorAction, ResetFactoryDefaultsAction, \
    FluxAction, \
    FreezeProductionRatios, InverseIsochronAction, IsoEvolutionAction, ExtractionAction, RecallAction, \
    AnalysisTableAction, ClearAnalysisSetsAction, SubgroupIdeogramAction, HistoryIdeogramAction, HybridIdeogramAction, \
    MassSpecReducedAction, InterpretedAgeRecallAction
from pychron.pipeline.tasks.preferences import PipelinePreferencesPane


# ============= enthought library imports =======================


class PipelinePlugin(BaseTaskPlugin):
    name = 'Pipeline'
    id = 'pychron.pipeline.plugin'
    nodes = ExtensionPoint(List, id='pychron.pipeline.nodes')
    node_factories = ExtensionPoint(List, id='pychron.pipeline.node_factories')
    predefined_templates = ExtensionPoint(List, id='pychron.pipeline.predefined_templates')

    def _file_defaults_default(self):
        files = [('flux_constants', 'FLUX_CONSTANTS_DEFAULT', False)]
        return files

    def _pipeline_factory(self):
        model = self.application.get_service(SampleBrowserModel)
        iamodel = self.application.get_service(InterpretedAgeBrowserModel)
        dvc = self.application.get_service(DVC)

        from pychron.pipeline.tasks.task import PipelineTask

        t = PipelineTask(browser_model=model,
                         dvc=dvc,
                         interpreted_age_browser_model=iamodel,
                         application=self.application)
        t.engine.nodes = self.nodes
        t.engine.node_factories = self.node_factories
        t.engine.predefined_templates = self.predefined_templates
        t.engine.load_predefined_templates()
        return t

    def _browser_model_factory(self):
        return SampleBrowserModel(application=self.application)

    def _interpreted_age_browser_model_factory(self):
        dvc = self.application.get_service(DVC)
        return InterpretedAgeBrowserModel(application=self.application,
                                          dvc=dvc)

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

        def ideogram_menu():
            return SMenu(IdeogramAction(),
                         SubgroupIdeogramAction(),
                         HybridIdeogramAction(),
                         HistoryIdeogramAction(),

                         id='ideogram.menu', name='Ideogram')

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
                          SchemaAddition(factory=InterpretedAgeRecallAction,
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

                            SchemaAddition(factory=ideogram_menu,
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
                                            path=rg),
                             SchemaAddition(factory=MassSpecReducedAction,
                                            path=rg),
                             ]

        help_actions = [SchemaAddition(factory=ResetFactoryDefaultsAction,
                                       path='MenuBar/help.menu'),
                        SchemaAddition(factory=ClearAnalysisSetsAction,
                                       path='MenuBar/help.menu')]
        configure_recall = SchemaAddition(factory=ConfigureRecallAction,
                                          path='MenuBar/edit.menu')

        actions = recall_actions
        actions.extend(plotting_actions)
        actions.extend(reduction_actions)
        actions.extend(help_actions)
        # actions.extend(quick_series_actions)

        return [TaskExtension(task_id='pychron.pipeline.task',
                              actions=[configure_recall]),
                TaskExtension(actions=actions)]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.pipeline.task',
                            name='Pipeline',
                            accelerator='Ctrl+p',
                            factory=self._pipeline_factory)]

# ============= EOF =============================================
