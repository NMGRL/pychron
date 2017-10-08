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
from numpy import array, array_split
from traits.api import Str
from traitsui.api import View, UItem, EnumEditor

from pychron.core.helpers.datetime_tools import bin_timestamps
from pychron.pipeline.nodes.base import BaseNode
from pychron.processing.utils.grouping import group_analyses_by_key


def aliquot(x):
    return x.aliquot


def identifier(x):
    return x.identifier


def increment(x):
    return x.increment


def comment(x):
    return x.comment


class GroupingNode(BaseNode):
    by_key = Str
    keys = ('Aliquot', 'Identifier', 'Step', 'Comment')
    analysis_kind = 'unknowns'
    name = 'Grouping'
    title = 'Edit Grouping'

    # auto_configure = False
    _attr = 'group_id'

    def load(self, nodedict):
        self.by_key = nodedict.get('key', 'Identifier')

    def _to_template(self, d):
        d['key'] = self.by_key

    def _generate_key(self):
        if self.by_key == 'Aliquot':
            key = aliquot
        elif self.by_key == 'Identifier':
            key = identifier
        elif self.by_key == 'Step':
            key = increment
        elif self.by_key == 'Comment':
            key = comment

        return key

    def run(self, state):
        unks = getattr(state, self.analysis_kind)
        group_analyses_by_key(unks, key=self._generate_key(), attr=self._attr)

    def traits_view(self):
        v = View(UItem('by_key',
                       style='custom',
                       editor=EnumEditor(name='keys')),
                 width=300,
                 title=self.title,
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v


class GraphGroupingNode(GroupingNode):
    title = 'Edit Graph Grouping'
    name = 'Graphing Group'
    _attr = 'graph_id'


class BinNode(BaseNode):
    analysis_kind = 'unknowns'

    def run(self, state):
        unks = getattr(state, self.analysis_kind)

        key = lambda x: x.timestamp
        unks = sorted(unks, key=key)

        tol_hrs = 1
        # tol = 60 * 60 * tol_hrs

        ts = array([ai.timestamp for ai in unks])
        # dts = ediff1d(ts)
        # idxs = where(dts > tol)[0]
        idxs = bin_timestamps(ts, tol_hrs)
        if idxs:
            unks = array(unks)
            for i, ais in enumerate(array_split(unks, idxs + 1)):
                for ai in ais:
                    ai.group_id = i
        else:
            for ai in unks:
                ai.group_id = 0

# ============= EOF =============================================
