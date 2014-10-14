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
import os
from traits.api import Str
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.menu import Action
from pychron.core.helpers.filetools import list_directory2
from pychron.core.helpers.logger_setup import new_logger
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.extraction_line.extraction_line_manager import ExtractionLineManager
from pychron.extraction_line.tasks.extraction_line_task import ExtractionLineTask
from pychron.extraction_line.tasks.extraction_line_actions import RefreshCanvasAction
from pychron.extraction_line.tasks.extraction_line_preferences import ExtractionLinePreferencesPane
from pychron.paths import paths


class ProcedureAction(Action):
    script_path = Str

    def perform(self, event):
        task = event.task.application.get_task('pychron.pyscript.task', activate=False)

        #open extraction line task
        event.task.application.open_task('pychron.extraction_line')

        root = os.path.dirname(self.script_path)
        name = os.path.basename(self.script_path)

        task.execution_context = {'analysis_type': 'blank' if 'blank' in name else 'unknown'}

        task.execute_script(name, root)


def procedure_action(name):
    a = ProcedureAction(id='procedures.action.{}'.format(name),
                        name=name.capitalize(),
                        script_path=os.path.join(paths.procedures_dir, name))
    return lambda: a


logger = new_logger('ExtractionLinePlugin')


class ExtractionLinePlugin(BaseTaskPlugin):
    id = 'pychron.extraction_line'

    #    manager = Instance(ExtractionLineManager)
    def _my_task_extensions_default(self):
        ex = [TaskExtension(actions=[SchemaAddition(id='refresh_canvas',
                                                    factory=RefreshCanvasAction,
                                                    path='MenuBar/tools.menu')])]

        if self.application.get_plugin('pychron.pyscript.plugin'):
            actions = []
            for f in list_directory2(paths.procedures_dir, extension='.py', remove_extension=True):
                actions.append(SchemaAddition(id='procedure.{}'.format(f),
                                              factory=procedure_action(f),
                                              path='MenuBar/procedures.menu'))

            if actions:
                actions.insert(0, SchemaAddition(id='procedures.menu',
                                                 before='window.menu',
                                                 after='tools.menu',
                                                 factory=lambda: SMenu(name='Procedures', id='procedures.menu'),
                                                 path='MenuBar'))

                ex.append(TaskExtension(actions=actions))
            else:
                logger.warning('no procedure scripts located in "{}"'.format(paths.procedures_dir))
        return ex

    def _service_offers_default(self):
        """
        """
        so = self.service_offer_factory(
            protocol=ExtractionLineManager,
            factory=self._factory
            #                            factory=ExtractionLineManager
        )

        #        so1 = self.service_offer_factory(
        #                          protocol = GaugeManager,
        #                          #protocol = GM_PROTOCOL,
        #                          factory = self._gm_factory)

        return [so]

    def _factory(self):
        from pychron.initialization_parser import InitializationParser

        ip = InitializationParser()
        try:
            plugin = ip.get_plugin('ExtractionLine', category='hardware')
            mode = ip.get_parameter(plugin, 'mode')
        #            mode = plugin.get('mode')
        except AttributeError:
            # no epxeriment plugin defined
            mode = 'normal'

        elm = ExtractionLineManager(mode=mode)
        elm.bind_preferences()
        return elm

    def _managers_default(self):
        """
        """
        return [
            dict(
                name='extraction_line',
                manager=self.application.get_service(ExtractionLineManager))]

    def _tasks_default(self):
        ts = [TaskFactory(id='pychron.extraction_line',
                          name='Extraction Line',
                          factory=self._task_factory,
                          accelerator='Ctrl+E',
                          task_group='hardware')]
        return ts

    def _task_factory(self):
        elm = self.application.get_service(ExtractionLineManager)
        t = ExtractionLineTask(manager=elm)
        return t

    def _preferences_panes_default(self):
        return [
            ExtractionLinePreferencesPane]

        #    def _my_task_extensions_default(self):

#        return [TaskExtension(actions=[SchemaAddition(id='Load Canvas',
#                                                      factory=LoadCanvasAction,
#                                                      path='MenuBar/ExtractionLine')])]
#============= EOF =============================================
