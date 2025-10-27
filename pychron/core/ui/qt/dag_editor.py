# ===============================================================================
# Copyright 2019 ross
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

from traits.api import List, Str
from traitsui.api import BasicEditorFactory
from traitsui.qt.editor import Editor

from pychron.core.ui.qt.dag import DAGraphView


class _DAGEditor(Editor):
    selected_commits = List

    def init(self, parent):
        self.sync_value(self.factory.selected, "selected_commits", "to")
        self.control = self._create_control(parent.parent())

    def _create_control(self, parent):
        return DAGraphView(None, self, parent)

    def update_editor(self):
        self.control.clear()
        self.control.set_commits(self.value)


class GitDAGEditor(BasicEditorFactory):
    klass = _DAGEditor
    selected = Str


# ============= EOF =============================================
