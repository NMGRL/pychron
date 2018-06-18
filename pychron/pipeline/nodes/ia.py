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

from pychron.pipeline.editors.set_ia_editor import SetInterpretedAgeEditor
from pychron.pipeline.nodes.data import DVCNode
from pychron.pipeline.subgrouping import make_interpreted_age_groups


class SetInterpretedAgeNode(DVCNode):
    name = 'Set Interpreted Age'

    configurable = False

    def run(self, state):
        unks = state.run_groups['unknowns']

        # ias = []
        #
        # def key(x):
        #     return x.subgroup['name'] if x.subgroup else ''
        #
        # for group in unks:
        #     ans = group.analyses
        #
        #     for subgroup, items in groupby(ans, key=key):
        #
        #         if subgroup:
        #             kind = subgroup['kind']
        #         else:
        #             kind = 'weighted_mean'
        #
        #         ag = InterpretedAgeGroup(analyses=list(items), preferred_age_kind=kind)
        #         ias.append(ag)
        nans = []
        for group in unks:
            ias = make_interpreted_age_groups(group.analyses)
            nans.extend(ias)

        editor = SetInterpretedAgeEditor()
        editor.set_items(ias)
        state.editors.append(editor)

# ============= EOF =============================================
