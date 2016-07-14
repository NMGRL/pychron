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
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import Any

from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.media_server.tasks.media_server_panes import ViewPane, TreePane


# ============= standard library imports ========================
# ============= local library imports  ==========================

class MediaServerTask(BaseManagerTask):
    browser = Any
    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.media_server.images'))

    def create_central_pane(self):
        return ViewPane(model=self.browser)
    def create_dock_panes(self):
        return [
                TreePane(
                         model=self.browser
                         )
                ]

# ============= EOF =============================================
