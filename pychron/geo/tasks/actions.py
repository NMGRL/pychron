# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from pyface.action.action import Action
from pyface.tasks.action.task_action import TaskAction

# ============= standard library imports ========================
# ============= local library imports  ==========================

class ExportStratCanvasAction(Action):
    name = 'Export Strat Canvas...'
    accelerator = 'Ctrl+.'
    method = 'export_strat_canvas'

    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.geo', activate=False)
        if hasattr(task, self.method):
            getattr(task, self.method)()


class ExportShapefileAction(TaskAction):
    name = 'Export Shapefile...'
    method = 'export_shapefile'

# ============= EOF =============================================

