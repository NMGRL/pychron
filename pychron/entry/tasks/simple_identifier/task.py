# ===============================================================================
# Copyright 2017 ross
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
from pyface.tasks.task_layout import TaskLayout, PaneItem

from pychron.entry.simple_identifier_manager import SimpleIdentifierManager
from pychron.entry.tasks.simple_identifier.panes import SimpleIdentifierPane, SimpleIdentifierEditorPane
from pychron.envisage.tasks.base_task import BaseManagerTask


class SimpleIdentifierTask(BaseManagerTask):
    id = 'pychron.entry.simple_identifier.task'
    name = 'Simple Identifier'

    def activated(self):
        self.manager.activated()

    def prepare_destroy(self):
        self.manager.prepare_destroy()

    def create_central_pane(self):
        return SimpleIdentifierPane(model=self.manager)

    def create_dock_panes(self):
        return [SimpleIdentifierEditorPane(model=self.manager)]

    def _manager_default(self):
        return SimpleIdentifierManager()

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.simple_identifier.editor'))

# ============= EOF =============================================
