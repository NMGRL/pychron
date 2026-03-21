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
from pychron.envisage.browser.interpreted_age_browser_model import (
    InterpretedAgeBrowserModel,
)
from pychron.envisage.browser.sample_browser_model import SampleBrowserModel
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.pipeline.tasks.actions import (
    ConfigureRecallAction,
    IdeogramAction,
    SpectrumAction,
    SeriesAction,
    BlanksAction,
    ICFactorAction,
    ResetFactoryDefaultsAction,
    FluxAction,
    FreezeProductionRatios,
    InverseIsochronAction,
    IsoEvolutionAction,
    ExtractionAction,
    RecallAction,
    AnalysisTableAction,
    ClearAnalysisSetsAction,
    SubgroupIdeogramAction,
    HistoryIdeogramAction,
    HybridIdeogramAction,
    MassSpecReducedAction,
    InterpretedAgeRecallAction,
    IdentifyPeaksDemoAction,
    ImportOptionsActions,
    DVCRecallAction,
    SignalEstimatorAction,
    DataReductionLogAction,
    IsochronSandboxAction,
    RunAction,
    RunFromAction,
    ClearAction,
    ResetAction,
)
from pychron.pipeline.tasks.preferences import PipelinePreferencesPane


# ============= enthought library imports =======================


class PipelinePlugin(BaseTaskPlugin):
    name = "Pipeline"
    id = "pychron.pipeline.plugin"
    nodes = ExtensionPoint(List, id="pychron.pipeline.nodes")
    node_factories = ExtensionPoint(List, id="pychron.pipeline.node_factories")
    predefined_templates = ExtensionPoint(
        List, id="pychron.pipeline.predefined_templates"
    )
    pipeline_group_icon_map = ExtensionPoint(
        List, id="pychron.pipeline.pipeline_group_icon_map"
    )

    def _help_tips_default(self):
        return []

    def _file_defaults_default(self):
        files = [("flux_constants", "FLUX_CONSTANTS_DEFAULT", False)]
        return files

    def _pipeline_factory(self):
        model = self.application.get_service(SampleBrowserModel)
        iamodel = self.application.get_service(InterpretedAgeBrowserModel)
        dvc = self.application.get_service(DVC)

        from pychron.pipeline.tasks.task import PipelineTask

        t = PipelineTask(
            browser_model=model,
            dvc=dvc,
            interpreted_age_browser_model=iamodel,
            application=self.application,
        )
        t.engine.nodes = self.nodes
        t.engine.node_factories = self.node_factories
        t.engine.predefined_templates = self.predefined_templates

        im = {
            "Table": "table",
            "Plot": "chart_curve",
            "Scripting": "script",
            "Edit": "toolbox",
            "Fit": "bricks",
            "Transfer": "network-transmit",
            "History": "edit-history-2",
            "Share": "share",
        }
        # convert the extension point into a dict
        im.update(self.pipeline_group_icon_map)
        t.engine.pipeline_group_icon_map = im
        t.engine.load_predefined_templates()
        return t

    def _browser_model_factory(self):
        return SampleBrowserModel(application=self.application)

    def _interpreted_age_browser_model_factory(self):
        dvc = self.application.get_service(DVC)
        return InterpretedAgeBrowserModel(application=self.application, dvc=dvc)

    # defaults
    def _service_offers_default(self):
        so = self.service_offer_factory(
            protocol=SampleBrowserModel, factory=self._browser_model_factory
        )

        so1 = self.service_offer_factory(
            protocol=InterpretedAgeBrowserModel,
            factory=self._interpreted_age_browser_model_factory,
        )
        return [so, so1]

    def _preferences_panes_default(self):
        return [PipelinePreferencesPane]

    def _task_extensions_default(self):
        def data_menu():
            return SMenu(id="data.menu", name="Data")

        def ideogram_menu():
            return SMenu(id="ideogram.menu", name="Ideogram")

        def plot_group():
            return SGroup(id="plot.group")

        def reduction_group():
            return SGroup(id="reduction.group")

        def recall_group():
            return SGroup(id="recall.group")

        def run_group():
            return SGroup(id="run.group")

        exts = self._get_extensions()
        extensions = [
            TaskExtension(actions=actions, task_id=eid) for eid, actions in exts
        ]

        additions = [
            SchemaAddition(
                factory=data_menu,
                path="MenuBar",
                before="tools.menu",
                after="view.menu",
            )
        ]

        for s, f, p in (
            ("ideogram", ideogram_menu, "MenuBar/data.menu/plot.group"),
            ("plot", plot_group, "MenuBar/data.menu"),
            ("fit", reduction_group, "MenuBar/data.menu"),
            ("recall", recall_group, "MenuBar/data.menu"),
            ("run", run_group, "MenuBar/data.menu"),
        ):
            for eid, actions in exts:
                for ai in actions:
                    if ai.id.startswith("pychron.pipeline.{}".format(s)):
                        additions.append(SchemaAddition(factory=f, path=p))
                        break

        extensions.append(TaskExtension(actions=additions))

        debug_additions = [
            SchemaAddition(factory=IdentifyPeaksDemoAction, path="MenuBar/tools.menu"),
            SchemaAddition(factory=ImportOptionsActions, path="MenuBar/tools.menu"),
            SchemaAddition(factory=SignalEstimatorAction, path="MenuBar/tools.menu"),
        ]
        extensions.append(
            TaskExtension(actions=debug_additions, task_id="pychron.pipeline.task")
        )
        return extensions

    def _available_task_extensions_default(self):
        def idformat(tag):
            return "pychron.pipeline.{}".format(tag)

        pg = "MenuBar/data.menu/plot.group"
        rg = "MenuBar/data.menu/reduction.group"
        ig = "MenuBar/data.menu/plot.group/ideogram.menu"
        reg = "MenuBar/data.menu/recall.group"
        rung = "MenuBar/data.menu/run.group"

        fit_actions = []
        for f, t in (
            (IsoEvolutionAction, "iso_evo"),
            (BlanksAction, "blanks"),
            (ICFactorAction, "icfactor"),
            (FluxAction, "flux"),
            (AnalysisTableAction, "table"),
            (FreezeProductionRatios, "freeze_production"),
            (MassSpecReducedAction, "mass_spec_reduced"),
            (DataReductionLogAction, "data_reduction_log"),
        ):
            fit_actions.append(
                SchemaAddition(
                    factory=f, id="pychron.pipeline.fit.{}".format(t), path=rg
                )
            )
        plot_actions = []
        for f, t in (
            (IdeogramAction, "ideogram"),
            (SubgroupIdeogramAction, "subgroup_ideogram"),
            (HybridIdeogramAction, "hybrid_ideogram"),
            (HistoryIdeogramAction, "history_ideogram"),
        ):
            plot_actions.append(
                SchemaAddition(
                    factory=f, id="pychron.pipeline.ideogram.{}".format(t), path=ig
                )
            )

        for f, t in (
            (SpectrumAction, "spectrum"),
            (InverseIsochronAction, "inverse_isochron"),
            (SeriesAction, "series"),
            (ExtractionAction, "extraction"),
            (IsochronSandboxAction, "isochron_sandbox"),
        ):
            plot_actions.append(
                SchemaAddition(
                    factory=f, id="pychron.pipeline.plot.{}".format(t), path=pg
                )
            )

        recall_actions = [
            SchemaAddition(
                factory=ConfigureRecallAction,
                id="pychron.pipeline.recall.configure",
                path="MenuBar/edit.menu",
            )
        ]

        for f, t in (
            (RecallAction, "recall"),
            (InterpretedAgeRecallAction, "interpreted_age_recall"),
            (DVCRecallAction, "dvc_recall"),
        ):
            recall_actions.append(
                SchemaAddition(
                    factory=f, id="pychron.pipeline.recall.{}".format(t), path=reg
                )
            )

        return [
            (
                self.id,
                "",
                "Pipeline Tools",
                [
                    SchemaAddition(
                        id=idformat("reset_factory_defaults"),
                        factory=ResetFactoryDefaultsAction,
                        path="MenuBar/help.menu",
                    ),
                    SchemaAddition(
                        id=idformat("clear_analysis_sets"),
                        factory=ClearAnalysisSetsAction,
                        path="MenuBar/help.menu",
                    ),
                ],
            ),
            ("{}.plot".format(self.id), "", "Plot", plot_actions),
            ("{}.fit".format(self.id), "", "Fit", fit_actions),
            ("{}.recall".format(self.id), "", "Recall", recall_actions),
        ]

    def _tasks_default(self):
        return [
            TaskFactory(
                id="pychron.pipeline.task",
                name="Pipeline",
                accelerator="Ctrl+p",
                factory=self._pipeline_factory,
            )
        ]


# ============= EOF =============================================
