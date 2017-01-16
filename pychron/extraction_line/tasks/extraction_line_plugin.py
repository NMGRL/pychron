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
import os

from envisage.extension_point import ExtensionPoint
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu, SGroup
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import List, Dict

from pychron.core.helpers.filetools import list_directory2
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.envisage.tasks.list_actions import ProcedureAction
from pychron.extraction_line.extraction_line_manager import ExtractionLineManager
from pychron.extraction_line.ipyscript_runner import IPyScriptRunner
from pychron.extraction_line.pyscript_runner import PyScriptRunner
from pychron.extraction_line.tasks.extraction_line_actions import RefreshCanvasAction
from pychron.extraction_line.tasks.extraction_line_preferences import ExtractionLinePreferencesPane, \
    ConsolePreferencesPane
from pychron.extraction_line.tasks.extraction_line_task import ExtractionLineTask
from pychron.paths import paths


def procedure_action(name, application):
    a = ProcedureAction(id='procedures.action.{}'.format(name),
                        name=name.capitalize(),
                        application=application,
                        script_path=os.path.join(paths.procedures_dir, name))
    return lambda: a


class ExtractionLinePlugin(BaseTaskPlugin):
    id = 'pychron.extraction_line'
    name = 'ExtractionLine'
    extraction_line_manager_klass = ExtractionLineManager
    plugin_canvases = ExtensionPoint(List(Dict),
                                     id='pychron.extraction_line.plugin_canvases')

    def _preferences_default(self):
        return self._preferences_factory('extractionline')

    # def set_preference_defaults(self):
    #     self._set_preference_defaults((('canvas_path', os.path.join(paths.canvas2D_dir, 'canvas.xml')),
    #                                    ('canvas_config_path', os.path.join(paths.canvas2D_dir, 'canvas_config.xml')),
    #                                    ('valves_path', os.path.join(paths.extraction_line_dir, 'valves.xml'))),
    #                                    'pychron.extraction_line')

    def test_gauge_communication(self):
        return self._test('test_gauge_communication')

    def test_valve_communication(self):
        return self._test('test_valve_communication')

    def _test(self, func):

        man = self.application.get_service(ExtractionLineManager)
        return getattr(man, func)()

    def _factory(self):
        elm = self.extraction_line_manager_klass(application=self.application)
        elm.bind_preferences()
        elm.plugin_canvases = self.plugin_canvases

        return elm

    def _runner_factory(self):
        runner = PyScriptRunner()
        return runner

    # defaults
    def _task_extensions_default(self):
        ex = [TaskExtension(actions=[SchemaAddition(id='refresh_canvas',
                                                    factory=RefreshCanvasAction,
                                                    path='MenuBar/tools.menu')])]

        if self.application.get_plugin('pychron.pyscript.plugin'):

            actions = []
            for f in list_directory2(paths.procedures_dir, extension='.py', remove_extension=True):
                actions.append(SchemaAddition(id='procedure.{}'.format(f),
                                              factory=procedure_action(f, self.application),
                                              path='MenuBar/procedures.menu/extraction_line.group'))

            if actions:
                actions.insert(0, SchemaAddition(id='procedures.menu',
                                                 before='window.menu',
                                                 after='tools.menu',
                                                 factory=lambda: SMenu(name='Procedures', id='procedures.menu'),
                                                 path='MenuBar'))

                actions.insert(1, SchemaAddition(id='extraction_line.group',
                                                 factory=lambda: SGroup(name='ExtractionLine',
                                                                        id='extraction_line.group'),
                                                 path='MenuBar/procedures.menu'))
                ex.append(TaskExtension(actions=actions))
            else:
                self.warning('no procedure scripts located in "{}"'.format(paths.procedures_dir))
        return ex

    def _service_offers_default(self):
        """
        """
        so = self.service_offer_factory(
            protocol=ExtractionLineManager,
            factory=self._factory)
        so1 = self.service_offer_factory(
            protocol=IPyScriptRunner,
            factory=self._runner_factory)

        return [so, so1]

    def _managers_default(self):
        """
        """
        return [
            dict(
                name='extraction_line',
                plugin_name=self.name,
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
        t = ExtractionLineTask(manager=elm, application=self.application)
        return t

    def _preferences_panes_default(self):
        return [ExtractionLinePreferencesPane, ConsolePreferencesPane]

# ============= EOF =============================================
