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
from traits.api import Str
from traitsui.menu import Action
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import list_directory2
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.extraction_line.extraction_line_manager import ExtractionLineManager
from pychron.extraction_line.ipyscript_runner import IPyScriptRunner
from pychron.extraction_line.pyscript_runner import PyScriptRunner
from pychron.extraction_line.tasks.extraction_line_task import ExtractionLineTask
from pychron.extraction_line.tasks.extraction_line_actions import RefreshCanvasAction
from pychron.extraction_line.tasks.extraction_line_preferences import ExtractionLinePreferencesPane, \
    ConsolePreferencesPane
from pychron.paths import paths


class ProcedureAction(Action):
    script_path = Str

    def __init__(self, *args, **kw):
        super(ProcedureAction, self).__init__(*args, **kw)

        ex = self.application.get_plugin('pychron.experiment.plugin')
        if ex:
            ex = ex.experimentor.executor
            ex.on_trait_change(self._update_alive, 'alive')

    def _update_alive(self, new):
        self.enabled = not new

    def perform(self, event):
        app = event.task.application

        for tid in ('pychron.experiment.task', 'pychron.spectrometer'):
            task = app.task_is_open(tid)
            if task:
                # make sure extraction line canvas is visible
                task.show_pane('pychron.extraction_line.canvas_dock')
                break
        else:
            # open extraction line task
            app.open_task('pychron.extraction_line')

        manager = app.get_service('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')

        root = os.path.dirname(self.script_path)
        name = os.path.basename(self.script_path)

        info = lambda x: '======= {} ======='.format(x)

        manager.info(info('Started Procedure "{}"'.format(name)))

        task = app.get_task('pychron.pyscript.task', activate=False)
        context = {'analysis_type': 'blank' if 'blank' in name else 'unknown'}
        task.execute_script(name, root,
                            delay_start=1,
                            on_completion=lambda: manager.info(info('Finished Procedure "{}"'.format(name))),
                            context=context)


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

    def set_preference_defaults(self):
        self._set_preference_defaults((('canvas_path', os.path.join(paths.canvas2D_dir, 'canvas.xml')),
                                       ('canvas_config_path', os.path.join(paths.canvas2D_dir, 'canvas_config.xml')),
                                       ('valves_path', os.path.join(paths.extraction_line_dir, 'valves.xml'))),
                                      'pychron.extraction_line')

    def test_gauge_communication(self):
        return self._test('test_gauge_communication')

    def test_valve_communication(self):
        return self._test('test_valve_communication')

    def _test(self, func):

        man = self.application.get_service(ExtractionLineManager)
        c = getattr(man, func)()
        return 'Passed' if c else 'Failed'

    def _factory(self):
        elm = self.extraction_line_manager_klass(application=self.application)
        elm.bind_preferences()

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
                                              path='MenuBar/procedures.menu'))

            if actions:
                actions.insert(0, SchemaAddition(id='procedures.menu',
                                                 before='window.menu',
                                                 after='tools.menu',
                                                 factory=lambda: SMenu(name='Procedures', id='procedures.menu'),
                                                 path='MenuBar'))

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
        t = ExtractionLineTask(manager=elm)
        return t

    def _preferences_panes_default(self):
        return [ExtractionLinePreferencesPane, ConsolePreferencesPane]

# ============= EOF =============================================
