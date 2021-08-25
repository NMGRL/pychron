# ===============================================================================
# Copyright 2021 ross
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
from pychron.pipeline.editors.recent_runs_editor import RecentRunsEditor
from pychron.pipeline.nodes.data import DVCNode


class RecentRunsNode(DVCNode):
    configurable = False

    def run(self, state):
        editor = self._editor_factory()
        editor.initialize()
        state.editors.append(editor)

    def _editor_factory(self):
        ed = RecentRunsEditor(dvc=self.dvc)
        return ed
# ============= EOF =============================================
