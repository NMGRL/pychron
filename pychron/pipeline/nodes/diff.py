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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.editors.diff_editor import DiffEditor
from pychron.pipeline.nodes.mass_spec import BaseMassSpecNode


class DiffNode(BaseMassSpecNode):
    name = "Diff"

    configurable = False
    auto_configure = False

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
