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
from operator import attrgetter

from traits.api import Str
from traitsui.api import View, UItem, EnumEditor

from itertools import groupby
from numpy import array, array_split

from pychron.core.helpers.datetime_tools import bin_timestamps
from pychron.pipeline.nodes.base import BaseNode


def group_analyses_by_key(items, key, attr='group_id'):
    if isinstance(key, str):
        keyfunc = lambda x: getattr(x, key)
    else:
        keyfunc = key

    ids = []
    for it in items:
        v = keyfunc(it)
        if v not in ids:
            ids.append(v)

    sitems = sorted(items, key=keyfunc)
    for k, analyses in groupby(sitems, key=keyfunc):
        gid = ids.index(k)
        for it in analyses:
            setattr(it, attr, gid)


class GroupingNode(BaseNode):
    by_key = Str
    keys = ('Aliquot', 'Identifier', 'Step', 'Comment', 'No Grouping')
    analysis_kind = 'unknowns'
    name = 'Grouping'
    title = 'Edit Grouping'

    _attr = 'group_id'

    def load(self, nodedict):
        self.by_key = nodedict.get('key', 'Identifier')

    def _to_template(self, d):
        d['key'] = self.by_key

    def _generate_key(self):
        if self.by_key in ('Aliquot', 'Identifier', 'Step', 'Comment'):
            key = attrgetter(self.by_key.lower())
            return key

    def run(self, state):
        if self.by_key != 'No Grouping':
            unks = getattr(state, self.analysis_kind)
            for unk in unks:
                unk.group_id = 0

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

        ts = array([ai.timestamp for ai in unks])

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
