# ===============================================================================
# Copyright 2018 ross
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

from pychron.pipeline.editors.group_age_editor import GroupAgeEditor
from pychron.pipeline.nodes.data import BaseDVCNode


class GroupAgeNode(BaseDVCNode):
    name = 'Group Age'
    auto_configure = False
    configurable = False
    editor_klass = GroupAgeEditor
    editor = None

    def run(self, state):
        unknowns = list(a for a in state.unknowns if a.analysis_type == 'unknown')

        editor = self.editor_klass(dvc=self.dvc)
        editor.items = unknowns
        editor.make_groups()
        state.editors.append(editor)
        self.editor = editor
        self.set_groups(state)

    def set_groups(self, state):
        pass

    def resume(self, state):
        # key = attrgetter('group_id')
        # nans = []

        # for gid, ans in groupby(sorted(state.unknowns, key=key), key=key):
        #     ias = make_interpreted_age_groups(ans)
        #     nans.extend(ias)

        # nans = self.editor.fgroups
        # state.unknowns = nans
        state.run_groups['unknowns'] = self.editor.groups
        state.unknowns = self.editor.unknowns
# ============= EOF =============================================
