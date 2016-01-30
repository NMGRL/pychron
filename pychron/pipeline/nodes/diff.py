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
from traits.api import Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.editors.diff_editor import DiffEditor


class DiffNode(BaseNode):
    name = 'Diff'

    auto_configure = False
    recaller = Any

    def run(self, state):
        if state.unknowns:
            self.unknowns = state.unknowns
            self.recaller.connect()
            for left in state.unknowns:
                editor = DiffEditor(recaller=self.recaller)
                left.load_raw_data()
                if editor.setup(left):
                    editor.set_diff(left)
                    state.editors.append(editor)
# ============= EOF =============================================
