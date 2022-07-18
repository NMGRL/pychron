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
from apptools.preferences.preference_binding import bind_preference

from pychron.core.helpers.iterfuncs import groupby_group_id
from pychron.pipeline.editors.group_age_editor import SubGroupAgeEditor
from pychron.pipeline.nodes.data import BaseDVCNode
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup
from pychron.pychron_constants import UNKNOWN, BLANK_TYPES, AIR


class GroupAgeNode(BaseDVCNode):
    name = "Group Age"
    auto_configure = False
    configurable = False
    editor = None
    editor_klass = SubGroupAgeEditor

    def bind_preferences(self):
        bind_preference(self, "skip_meaning", "pychron.pipeline.skip_meaning")

    def run(self, state):
        unknowns = list(a for a in state.unknowns if a.analysis_type == "unknown")

        editor = self.editor_klass(dvc=self.dvc)
        editor.load()
        editor.items = unknowns
        editor.arar_calculation_options = state.arar_calculation_options
        editor.make_groups()
        state.editors.append(editor)
        self.editor = editor
        self.set_groups(state)

    def set_groups(self, state):
        def factory(ans, tag="Human Table"):
            if self.skip_meaning:
                if tag in self.skip_meaning:
                    ans = (ai for ai in ans if ai.tag.lower() != "skip")

            g = InterpretedAgeGroup(analyses=list(ans))
            return g

        unknowns = list(a for a in state.unknowns if a.analysis_type == UNKNOWN)
        blanks = (a for a in state.unknowns if a.analysis_type in BLANK_TYPES)
        airs = (a for a in state.unknowns if a.analysis_type == AIR)

        # unk_group = [factory(analyses) for _, analyses in groupby(sorted(unknowns, key=key), key=key)]
        blank_group = [factory(analyses) for _, analyses in groupby_group_id(blanks)]
        air_group = [factory(analyses) for _, analyses in groupby_group_id(airs)]
        munk_group = [
            factory(analyses, "Machine Table")
            for _, analyses in groupby_group_id(unknowns)
        ]

        groups = {
            # 'unknowns': unk_group,
            "blanks": blank_group,
            "airs": air_group,
            "machine_unknowns": munk_group,
        }

        state.run_groups = groups

    def resume(self, state):
        # key = attrgetter('group_id')
        # nans = []

        # for gid, ans in groupby(sorted(state.unknowns, key=key), key=key):
        #     ias = make_interpreted_age_groups(ans)
        #     nans.extend(ias)

        # nans = self.editor.fgroups
        # state.unknowns = nans
        state.run_groups["unknowns"] = self.editor.groups
        state.unknowns = self.editor.unknowns
        self.editor.dump()


# ============= EOF =============================================
