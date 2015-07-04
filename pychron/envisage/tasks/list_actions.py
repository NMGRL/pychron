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
from traits.api import Str
# ============= standard library imports ========================
import os

# ============= local library imports  ==========================
from traitsui.menu import Action
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager


class ListAction(Action):
    pass


class PatternAction(ListAction):
    pattern_path = Str
    manager_name = Str

    def perform(self, event):
        app = event.task.application
        man = app.get_service(ILaserManager, 'name=="{}"'.format(self.manager_name))
        man.execute_pattern(self.pattern_path)


class ProcedureAction(ListAction):
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

# ============= EOF =============================================
