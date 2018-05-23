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

from pychron.pipeline.editors.group_age_editor import GroupAgeEditor
from pychron.pipeline.nodes.data import BaseDVCNode
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup


class GroupAgeNode(BaseDVCNode):
    name = 'Group Age'
    auto_configure = False
    configurable = False
    editor_klass = GroupAgeEditor

    def run(self, state):
        unknowns = list(a for a in state.unknowns if a.analysis_type == 'unknown')

        editor = self.editor_klass(dvc=self.dvc)
        editor.items = unknowns
        state.editors.append(editor)
        self.set_groups(state)

    def set_groups(self, state):
        pass

    def resume(self, state):
        key = attrgetter('group_id')
        nans = []
        for gid, ans in groupby(sorted(state.unknowns, key=key), key=key):
            ans = list(ans)

            key = attrgetter('subgroup')

            for subgroup, items in groupby(ans, key=key):
                items = list(items)
                if subgroup:
                    kind = '_'.join(subgroup.split('_')[:-1])
                else:
                    kind = 'weighted_mean'

                ag = InterpretedAgeGroup(analyses=items)
                ag.record_id = '{:02n}{}'.format(ag.aliquot, kind[0])

                ag.get_age(kind, set_preferred=True)
                nans.append(ag)

        state.unknowns = nans

# ============= EOF =============================================
