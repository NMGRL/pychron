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

from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.tasks.action.task_action import TaskAction

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.view_util import open_view
from pychron.logger.logviewer import LogViewer, LogModel, TwistedLogModel
from pychron.paths import paths


class LogViewerAction(TaskAction):
    name = 'Open Log Viewer...'
    path = None

    def perform(self, event):
        path = self.path
        if path is None:
            dlg = FileDialog(action='open',
                             wildcard='*.log;*.json|log|*.json',
                             default_directory=paths.log_dir)
            if dlg.open() == OK:
                path = dlg.path

        if path:
            klass = TwistedLogModel if path.endswith('.json') else LogModel
            lm = klass()
            lm.open_file(path)
            lv = LogViewer(model=lm)
            open_view(lv)


class CurrentLogViewerAction(LogViewerAction):
    name = 'Current Log Viewer'
    path = os.path.join(paths.log_dir, 'pychron.current.log')

# ============= EOF =============================================
