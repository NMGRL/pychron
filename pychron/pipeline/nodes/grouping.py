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

from operator import attrgetter

from numpy import array, array_split
# ============= enthought library imports =======================
from traits.api import Str, Enum
from traitsui.api import UItem, EnumEditor, VGroup

from pychron.core.helpers.datetime_tools import bin_timestamps
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.pipeline.grouping import group_analyses_by_key
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.subgrouping import apply_subgrouping, compress_groups
from pychron.processing.analyses.preferred import get_preferred_grp, Preferred
from pychron.pychron_constants import SUBGROUPING_ATTRS, WEIGHTED_MEAN, \
    MSEM, SD, DEFAULT_INTEGRATED


class GroupingNode(BaseNode):
    by_key = Str
    keys = ('Aliquot', 'Comment', 'Identifier', 'Sample', 'Step', 'SubGroup', 'No Grouping')
    analysis_kind = 'unknowns'
    name = 'Grouping'
    title = 'Edit Grouping'

    attribute = Enum('Group', 'Graph', 'Tab')
    # _attr = 'group_id'
    _id_func = None

    _sorting_enabled = True
    _cached_items = None
    _state = None
    _parent_group = None

    def load(self, nodedict):
        self.by_key = nodedict.get('key', 'Identifier')

    def _to_template(self, d):
        d['key'] = self.by_key

    def _generate_key(self):
        if self.by_key != 'No Grouping':
            return attrgetter(self.by_key.lower())

    def run(self, state):
        self._run(state)

    def post_run(self, engine, state):
        self._state = None

    def _run(self, state):
        unks = getattr(state, self.analysis_kind)
        self._state = state

        # print('clearsd', self._attr)
        for unk in unks:
            self._clear_grouping(unk)

        if self.by_key != 'No Grouping':
            key = self._generate_key()
            items = group_analyses_by_key(unks, key=key, attr=self._attr, id_func=self._id_func,
                                          sorting_enabled=self._sorting_enabled,
                                          parent_group=self._parent_group)

            setattr(state, self.analysis_kind, items)
            setattr(self, self.analysis_kind, items)

    def _clear_grouping(self, unk):
        setattr(unk, self._attr, 0)

    @property
    def _attr(self):
        return '{}_id'.format(self.attribute.lower())

    def traits_view(self):
        kgrp = VGroup(UItem('by_key',
                            style='custom',
                            editor=EnumEditor(name='keys')),
                      show_border=True,
                      label='Key')

        agrp = VGroup(UItem('attribute',
                            tooltip='Group=Display all groups on a single graph\n'
                                    'Graph=Display groups on separate graphs\n'
                                    'Tab=Display groups on separate tabs'), label='To Group', show_border=True)
        v = okcancel_view(VGroup(agrp, kgrp),
                          width=300,
                          title=self.title,
                          )
        return v


class GraphGroupingNode(GroupingNode):
    title = 'Edit Graph Grouping'
    name = 'Graphing Group'
    _attr = 'graph_id'


class SubGroupingNode(GroupingNode, Preferred):
    title = 'Edit SubGrouping'
    keys = ('Aliquot', 'Identifier', 'Step', 'Comment', 'No Grouping')
    name = 'SubGroup'
    by_key = 'Aliquot'
    attribute = 'subgroup'

    # include_j_error_in_individual_analyses = Bool(False)
    # include_j_error_in_mean = Bool(True)

    _sorting_enabled = False
    _parent_group = 'group_id'

    def load(self, nodedict):
        self.by_key = nodedict.get('key', 'Aliquot')

    def _clear_grouping(self, unk):
        unk.subgroup = None

    def _id_func(self, gid, analyses):
        analyses = list(analyses)
        naliquots = len({a.aliquot for a in analyses})
        for attr in SUBGROUPING_ATTRS:
            if attr == 'age':
                continue

            pv = self._get_pv(attr)
            if attr == 'age':
                kind, error = WEIGHTED_MEAN, MSEM
            else:
                kind = WEIGHTED_MEAN if naliquots > 1 else DEFAULT_INTEGRATED
                error = MSEM if naliquots > 1 else SD

            pv.kind = kind
            pv.error_kind = error

        grouping = {'{}_kind'.format(pv.attr): pv.kind for pv in self.preferred_values}
        grouping.update({'{}_error_kind'.format(pv.attr): pv.error_kind for pv in self.preferred_values})

        apply_subgrouping(grouping, analyses, gid=gid)

    def _pre_run_hook(self, state):
        # unks = getattr(state, self.analysis_kind)
        self._run(state)

    def _by_key_changed(self):
        if self._state:
            self._run(self._state)

    def run(self, state):
        self._run(state)

        ans = getattr(state, self.analysis_kind)
        compress_groups(ans)

    def traits_view(self):

        v = okcancel_view(VGroup(VGroup(UItem('by_key',
                                              style='custom',
                                              editor=EnumEditor(name='keys')),
                                        show_border=True, label='Grouping'),

                                 get_preferred_grp(label='Types', show_border=True)),
                          width=500,
                          resizable=True,
                          title=self.title)
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
