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
import os

from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.action.schema import SMenu, SGroup
from pyface.tasks.action.schema_addition import SchemaAddition
from pychron.core.helpers.filetools import add_extension
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.paths import paths
from pychron.pipeline.tasks.actions import ConfigureRecallAction, IdeogramAction, IsochronAction, SpectrumAction, \
    SeriesAction, BlanksAction, ICFactorAction, ResetFactoryDefaultsAction
from pychron.pipeline.tasks.browser_task import BrowserTask
from pychron.pipeline.tasks.preferences import PipelinePreferencesPane
from pychron.pipeline.tasks.task import PipelineTask
from pychron.envisage.browser.browser_model import BrowserModel
from pychron.pipeline.template import ICFACTOR, BLANKS, ISOEVO, SPEC, IDEO, ISOCHRON


class PipelinePlugin(BaseTaskPlugin):
    def start(self):
        super(PipelinePlugin, self).start()
        ov = False
        for p, t, overwrite in (('icfactor', ICFACTOR, ov),
                                ('blanks', BLANKS, ov),
                                ('iso_evo', ISOEVO, ov),
                                ('ideogram', IDEO, ov),
                                ('spectrum', SPEC, ov),
                                ('isochron', ISOCHRON, ov)):
            pp = os.path.join(paths.pipeline_template_dir,
                              add_extension(p, '.yaml'))

            if not os.path.isfile(pp) or overwrite:
                with open(pp, 'w') as wfile:
                    wfile.write(t)

    def _pipeline_factory(self):
        model = self.application.get_service(BrowserModel)
        t = PipelineTask(browser_model=model)
        return t

    def _browser_factory(self):
        model = self.application.get_service(BrowserModel)
        t = BrowserTask(browser_model=model)
        return t

    def _browser_model_factory(self):
        return BrowserModel(application=self.application)

    # defaults
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=BrowserModel,
                                        factory=self._browser_model_factory)
        return [so]

    def _preferences_panes_default(self):
        return [PipelinePreferencesPane]

    def _task_extensions_default(self):
        def data_menu():
            return SMenu(id='data.menu', name='Data')

        def plot_group():
            return SGroup(id='plot.group')

        def reduction_group():
            return SGroup(id='reduction.group')

        pg = 'MenuBar/data.menu/plot.group'
        rg = 'MenuBar/data.menu/reduction.group'
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
                            SchemaAddition(factory=IsochronAction,
                                           path=pg),
                            SchemaAddition(factory=SeriesAction,
                                           path=pg)]

        reduction_actions = [SchemaAddition(factory=reduction_group,
                                            path='MenuBar/data.menu'),
                             SchemaAddition(factory=BlanksAction,
                                            path=rg),
                             SchemaAddition(factory=ICFactorAction,
                                            path=rg)]
        help_actions = [SchemaAddition(factory=ResetFactoryDefaultsAction,
                                       path='MenuBar/help.menu')]
        configure_recall = SchemaAddition(factory=ConfigureRecallAction,
                                          path='MenuBar/Edit')
        browser_actions = [configure_recall]

        return [TaskExtension(task_id='pychron.pipeline.task',
                              actions=[configure_recall]),
                TaskExtension(task_id='pychron.browser.task',
                              actions=browser_actions),
                TaskExtension(actions=plotting_actions + reduction_actions + help_actions)]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.pipeline.task',
                            name='Pipeline',
                            accelerator='Ctrl+p',
                            factory=self._pipeline_factory),
                TaskFactory(id='pychron.browser.task',
                            name='Browser',
                            accelerator='Ctrl+b',
                            factory=self._browser_factory)
                ]

# ============= EOF =============================================
