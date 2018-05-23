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
from itertools import groupby
from operator import attrgetter

from pychron.pipeline.editors.set_ia_editor import SetInterpretedAgeEditor
from pychron.pipeline.nodes.data import DVCNode
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup


class SetInterpretedAgeNode(DVCNode):
    name = 'Set Interpreted Age'

    configurable = False

    def run(self, state):
        unks = state.groups['unknowns']

        ias = []
        for group in unks:
            key = attrgetter('subgroup')
            ans = group.analyses

            for subgroup, items in groupby(ans, key=key):
                if subgroup:
                    kind = '_'.join(subgroup.split('_')[:-1])
                else:
                    kind = 'weighted_mean'

                ag = InterpretedAgeGroup(analyses=list(items), preferred_age_kind=kind)
                ias.append(ag)

        editor = SetInterpretedAgeEditor()
        editor.set_items(ias)
        state.editors.append(editor)

# ============= EOF =============================================
