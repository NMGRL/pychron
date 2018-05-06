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

from traits.api import Str, Enum, Bool
from traitsui.api import View, UItem, EnumEditor, VGroup, Item

from itertools import groupby
from numpy import array, array_split

from pychron.core.helpers.datetime_tools import bin_timestamps
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.tagging import apply_subgrouping, compress_groups
from pychron.processing.analyses.analysis_group import AnalysisGroup, StepHeatAnalysisGroup, InterpretedAgeGroup


def group_analyses_by_key(items, key, attr='group_id', id_func=None):
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
        if id_func:
            gid = id_func(gid, analyses)
        for it in analyses:
            setattr(it, attr, gid)


class GroupingNode(BaseNode):
    by_key = Str
    keys = ('Aliquot', 'Identifier', 'Step', 'Comment', 'SubGroup', 'No Grouping')
    analysis_kind = 'unknowns'
    name = 'Grouping'
    title = 'Edit Grouping'

    _attr = 'group_id'
    _id_func = None
    mean_groups = Bool(False)
    meanify_enabled = Bool(True)

    def load(self, nodedict):
        self.by_key = nodedict.get('key', 'Identifier')
        self.meanify_enabled = nodedict.get('meanify_enabled', True)

    def _to_template(self, d):
        d['key'] = self.by_key

    def _generate_key(self):
        if self.by_key != 'No Grouping':
            return attrgetter(self.by_key.lower())

    def run(self, state):
        if self.by_key != 'No Grouping':
            unks = getattr(state, self.analysis_kind)
            for unk in unks:
                setattr(unk, self._attr, 0)

            key = self._generate_key()
            if self.mean_groups:
                gs = []
                for k, ans in groupby(sorted(unks, key=key), key=key):
                    a = InterpretedAgeGroup(analyses=list(ans))
                    if 'plateau' in k:
                        a.preferred_age_kind = 'plateau'
                    gs.append(a)
                setattr(state, self.analysis_kind, gs)
            else:
                group_analyses_by_key(unks, key=self._generate_key(), attr=self._attr, id_func=self._id_func)

    def traits_view(self):
        v = View(UItem('by_key',
                       style='custom',
                       editor=EnumEditor(name='keys')),
                 Item('mean_groups', label='Meanify Groups',
                      visible_when='meanify_enabled',
                      enabled_when='by_key=="SubGroup"'),
                 width=300,
                 title=self.title,
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v


class GraphGroupingNode(GroupingNode):
    title = 'Edit Graph Grouping'
    name = 'Graphing Group'
    _attr = 'graph_id'


class SubGroupingNode(GroupingNode):
    title = 'Edit SubGrouping'
    keys = ('Aliquot', 'Identifier', 'Step', 'Comment', 'No Grouping')
    name = 'SubGroup'
    by_key = 'Aliquot'
    _attr = 'subgroup'
    grouping_kind = Enum('Weighted Mean', 'Plateau', 'Isochron', 'Plateau else Weighted Mean', 'Integrated')

    def load(self, nodedict):
        self.by_key = nodedict.get('key', 'Aliquot')

    def _id_func(self, gid, analyses):
        tag = self.grouping_kind.lower().replace(' ', '_')

        apply_subgrouping(tag, list(analyses), gid=gid)

    def run(self, state):
        super(SubGroupingNode, self).run(state)

        ans = getattr(state, self.analysis_kind)
        compress_groups(ans)

    def traits_view(self):
        v = View(VGroup(VGroup(UItem('by_key',
                                     style='custom',
                                     editor=EnumEditor(name='keys')),
                               show_border=True, label='Grouping'),
                        VGroup(Item('grouping_kind', label='Grouping Type'), show_border=True)),
                 width=300,
                 title=self.title,
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v


class BinNode(BaseNode):
    analysis_kind = 'unknowns'

    def run(self, state):
        unks = getattr(state, self.analysis_kind)

        key = attrgetter('timestamp')
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
