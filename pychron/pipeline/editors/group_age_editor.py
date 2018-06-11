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

from pyface.action.menu_manager import MenuManager
from traits.api import Property, Str, Int, List
from traitsui.api import View, UItem, VGroup, HGroup, Handler, Tabbed, InstanceEditor
from traitsui.menu import Action

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.pipeline.editors.base_adapter import BaseAdapter
from pychron.pipeline.editors.base_table_editor import BaseTableEditor
from pychron.pipeline.subgrouping import apply_subgrouping, compress_groups, set_subgrouping_error, \
    make_interpreted_age_groups, make_interpreted_age_group
from pychron.processing.analyses.preferred import get_preferred_grp
from pychron.pychron_constants import MSEM, SEM, SD, WEIGHTED_MEAN, INTEGRATED


# ============= standard library imports ========================
# ============= local library imports  ==========================

class GroupAdapter(BaseAdapter):
    columns = [('Group', 'group_id'),
               ('Name', 'name')]


class SubGroupAdapter(BaseAdapter):
    columns = [('Group', 'group_id'),
               ('SubGroup', 'subgroup_id'),
               ('Label', 'label_name'),
               ('Name', 'name')
               ]


class GroupAgeAdapter(SubGroupAdapter):
    columns = [
        ('RunID', 'record_id'),
        ('Tag', 'tag'),
        ('Group', 'group_id'),
        ('SubGroup', 'subgroup'),
        #
        # ('Kind', 'age_kind'),
        # ('Error', 'age_error_kind'),
        #
        # # ('Age', 'age'),
        # # (PLUSMINUS_ONE_SIGMA, 'age_err'),
        #
        # ('K/Ca Kind', 'kca_kind'),
        # # ('K/Ca', 'kca'),
        #
        # ('K/Cl Kind', 'kcl_kind'),
        # # ('K/Cl', 'kcl'),
        #
        # ('%40Ar* Kind', 'rad40_percent_kind'),
        # # ('%40Ar*', 'rad40_percent'),
        # ('Mol 39K Kind', 'moles_k39_kind'),
        # ('Signal 39K Kind', 'signal_k39_kind'),
        # ('mol 39K', 'k39'),
    ]

    subgroup_text = Property
    record_id_width = Int(60)
    tag_width = Int(40)
    group_id_width = Int(60)
    subgroup_width = Int(100)

    # age_kind_text = Property
    # age_error_kind_text = Property
    #
    # kca_kind_text = Property
    # kca_error_kind_text = Property
    # kcl_kind_text = Property
    # kcl_error_kind_text = Property
    # rad40_percent_kind_text = Property
    # rad40_percent_error_kind_text = Property
    # moles_k39_kind_text = Property
    # moles_k39_error_kind_text = Property
    # signal_k39_kind_text = Property
    # signal_k39_error_kind_text = Property

    # def _get_age_kind_text(self):
    #     return self._get_subgroup_attr('age_kind')
    #
    # def _get_age_error_kind_text(self):
    #     return self._get_subgroup_attr('age_error_kind')
    #
    # def _get_kca_kind_text(self):
    #     return self._get_subgroup_attr('kca_kind')
    #
    # def _get_kca_error_kind_text(self):
    #     return self._get_subgroup_attr('kca_error_kind')
    #
    # def _get_kcl_kind_text(self):
    #     return self._get_subgroup_attr('kcl_kind')
    #
    # def _get_kcl_error_kind_text(self):
    #     return self._get_subgroup_attr('kcl_error_kind')
    #
    # def _get_rad40_percent_kind_text(self):
    #     return self._get_subgroup_attr('rad40_percent_kind')
    #
    # def _get_rad40_percent_error_kind_text(self):
    #     return self._get_subgroup_attr('rad40_percent_error_kind')
    #
    # def _get_moles_k39_kind_text(self):
    #     return self._get_subgroup_attr('moles_k39_kind')
    #
    # def _get_moles_k39_error_kind_text(self):
    #     return self._get_subgroup_attr('moles_k39_error_kind')
    #
    # def _get_signal_k39_kind_text(self):
    #     return self._get_subgroup_attr('signal_k39_kind')
    #
    # def _get_signal_k39_error_kind_text(self):
    #     return self._get_subgroup_attr('signal_k39_error_kind')
    def _get_subgroup_text(self):
        return self._get_subgroup_attr('name')

    def _get_subgroup_attr(self, attr):
        ret = ''
        if self.item.subgroup:
            ret = self.item.subgroup[attr]
        return ret

    def get_menu(self, obj, trait, row, column):
        age = MenuManager(Action(name='Calculate Wt. Mean', action='group_as_weighted_mean'),
                          Action(name='Calculate Plateau', action='group_as_plateau'),
                          Action(name='Calculate Plateau else Wt. Mean', action='group_as_plateau_else_weighted_mean'),
                          Action(name='Calculate Isochron', action='group_as_isochron'),
                          Action(name='Calculate Integrated', action='group_as_integrated'),
                          name='Age')

        error = MenuManager(Action(name=SD, action='group_sd'),
                            Action(name=SEM, action='group_sem'),
                            Action(name=MSEM, action='group_msem'),
                            name='Error')
        m = MenuManager(age,
                        error,
                        Action(name='Clear Grouping', action='clear_grouping'))
        return m


class THandler(Handler):
    def group_as_plateau_else_weighted_mean(self, info, obj):
        obj.group('Plateau else Weighted Mean')

    def group_as_weighted_mean(self, info, obj):
        obj.group(WEIGHTED_MEAN)

    def group_as_plateau(self, info, obj):
        obj.group('Plateau')

    def group_as_isochron(self, info, obj):
        obj.group('Isochron')

    def group_as_integrated(self, info, obj):
        obj.group(INTEGRATED)

    def clear_grouping(self, info, obj):
        obj.clear_grouping()

    def group_sd(self, info, obj):
        obj.group_sd()

    def group_sem(self, info, obj):
        obj.group_sem()

    def group_msem(self, info, obj):
        obj.group_msem()


class GroupAgeEditor(BaseTableEditor, ColumnSorterMixin):
    help_str = Str('Right-click to subgroup analyses and calculate an age')
    groups = List
    subgroups = List
    selected_group = List
    selected_subgroup = List
    selected_group_item = Property(depends_on='selected_group')
    selected_subgroup_item = Property(depends_on='selected_subgroup')

    def _get_selected_group_item(self):
        if self.selected_group:
            ret = self.selected_group[0]
            return ret

    def _get_selected_subgroup_item(self):
        if self.selected_subgroup:
            ret = self.selected_subgroup[0]
            return ret

    def make_groups(self):
        key = attrgetter('group_id')
        sgs = []
        gs = []
        for gid, ans in groupby(sorted(self.items, key=key), key=key):
            groups, analyses = make_interpreted_age_groups(ans)
            sgs.extend(groups)

            gs.append(make_interpreted_age_group(groups + analyses, gid))

        self.groups = gs
        self.subgroups = sgs

    def clear_grouping(self):
        if self.selected:
            for s in self.selected:
                s.subgroup = None

            compress_groups(self.items)

    def group_sd(self):
        self._group_error(SD)

    def group_sem(self):
        self._group_error(SEM)

    def group_msem(self):
        self._group_error(MSEM)

    def group(self, kind: object) -> object:
        self._group(kind)
        self.refresh_needed = True

    def _group_error(self, tag):
        if self.selected:
            set_subgrouping_error(tag, self.selected, self.items)
            self.refresh_needed = True

    def _group(self, tag):
        if self.selected:
            d = {'age_kind': tag, 'age_error_kind': MSEM}
            apply_subgrouping(d, self.selected, items=self.items)
            self.refresh_needed = True

    def traits_view(self):
        agrp = VGroup(HGroup(UItem('help_str', style='readonly'),
                             show_border=True, label='Info'),

                      UItem('items',
                            editor=myTabularEditor(adapter=GroupAgeAdapter(),
                                                   # col_widths='col_widths',
                                                   selected='selected',
                                                   multi_select=True,
                                                   auto_update=False,
                                                   refresh='refresh_needed',
                                                   operations=['delete', 'move'],
                                                   column_clicked='column_clicked')),
                      label='Analyses')

        sgrp = VGroup(UItem('subgroups', editor=myTabularEditor(adapter=SubGroupAdapter(),
                                                                multi_select=True,
                                                                selected='selected_subgroup')),
                      UItem('selected_subgroup_item',
                            style='custom', editor=InstanceEditor(view=View(get_preferred_grp()))),
                      label='SubGroups')

        ggrp = VGroup(UItem('groups',
                            style='custom', editor=myTabularEditor(adapter=GroupAdapter(),
                                                                   multi_select=True,
                                                                   selected='selected_group')),
                      UItem('selected_group_item',
                            style='custom', editor=InstanceEditor(view=View(get_preferred_grp()))),
                      label='Groups')

        v = View(Tabbed(agrp, sgrp, ggrp),

                 handler=THandler())
        return v

# ============= EOF =============================================
