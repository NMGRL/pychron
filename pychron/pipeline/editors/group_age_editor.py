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
from pyface.action.menu_manager import MenuManager
from traits.api import Property, Str, Int, List, on_trait_change
from traitsui.api import View, UItem, VGroup, Handler, InstanceEditor
from traitsui.menu import Action

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.helpers.iterfuncs import groupby_group_id
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.pipeline.editors.base_adapter import BaseAdapter
from pychron.pipeline.editors.base_table_editor import BaseTableEditor
from pychron.pipeline.subgrouping import compress_groups, make_interpreted_age_groups, make_interpreted_age_group
from pychron.processing.analyses.preferred import get_preferred_grp


# ============= standard library imports ========================
# ============= local library imports  ==========================

class GroupAdapter(BaseAdapter):
    columns = [('Group', 'group_id'),
               # ('Name', 'name'),
               ('Age Kind', 'age_kind'),
               ('Error', 'age_error_kind')
               ]

    group_id_width = Int(60)
    age_kind_text = Property
    age_error_kind_text = Property

    def _get_age_error_kind_text(self):
        pv = self.item.get_preferred_obj('age')
        return pv.error_kind

    def _get_age_kind_text(self):
        pv = self.item.get_preferred_obj('age')
        return pv.kind


class SubGroupAdapter(GroupAdapter):
    columns = [('Status', 'tag'),
               ('Group', 'group_id'),
               ('SubGroup', 'subgroup_id'),
               ('Label', 'label_name'),
               ('Age Kind', 'age_kind'),
               ('Error', 'age_error_kind')
               ]

    subgroup_id_width = Int(60)
    tag_width = Int(60)
    tag_text = Property

    def _get_tag_text(self):
        return 'Omit' if self.item.is_omitted() else 'Include'

    def get_menu(self, obj, trait, row, column):
        m = MenuManager(Action(name='Toggle Omit', action='toggle_omit'))
        return m


class AnalysesAdapter(SubGroupAdapter):
    columns = [
        ('RunID', 'record_id'),
        ('Tag', 'tag'),
        ('Group', 'group_id'),
        ('SubGroup', 'subgroup'),
    ]

    subgroup_text = Property
    record_id_width = Int(60)
    subgroup_width = Int(100)

    def _get_tag_text(self):
        return self.item.tag

    def _get_subgroup_text(self):
        return self._get_subgroup_attr('name')

    def _get_subgroup_attr(self, attr):
        ret = ''
        if self.item.subgroup:
            ret = self.item.subgroup[attr]
        return ret

    def get_menu(self, obj, trait, row, column):
        # age = MenuManager(Action(name='Calculate Wt. Mean', action='group_as_weighted_mean'),
        #                   Action(name='Calculate Plateau', action='group_as_plateau'),
        #                   Action(name='Calculate Plateau else Wt. Mean', action='group_as_plateau_else_weighted_mean'),
        #                   Action(name='Calculate Isochron', action='group_as_isochron'),
        #                   Action(name='Calculate Integrated', action='group_as_integrated'),
        #                   name='Age')
        #
        # error = MenuManager(Action(name=SD, action='group_sd'),
        #                     Action(name=SEM, action='group_sem'),
        #                     Action(name=MSEM, action='group_msem'),
        #                     name='Error')
        m = MenuManager(Action(name='Clear Grouping', action='clear_grouping'),
                        Action(name='Group Selected', action='group_selected'),
                        Action(name='SubGroup Selected', action='subgroup_selected'))
        return m


class THandler(Handler):
    # def group_as_plateau_else_weighted_mean(self, info, obj):
    #     obj.group('Plateau else Weighted Mean')
    #
    # def group_as_weighted_mean(self, info, obj):
    #     obj.group(WEIGHTED_MEAN)
    #
    # def group_as_plateau(self, info, obj):
    #     obj.group('Plateau')
    #
    # def group_as_isochron(self, info, obj):
    #     obj.group('Isochron')
    #
    # def group_as_integrated(self, info, obj):
    #     obj.group(INTEGRATED)
    #
    # def group_sd(self, info, obj):
    #     obj.group_sd()
    #
    # def group_sem(self, info, obj):
    #     obj.group_sem()
    #
    # def group_msem(self, info, obj):
    #     obj.group_msem()

    def group_selected(self, info, obj):
        obj.group_selected()

    def subgroup_selected(self, info, obj):
        obj.subgroup_selected()

    def clear_grouping(self, info, obj):
        if obj.selected:
            for s in obj.selected:
                s.subgroup = None

            compress_groups(obj.items)

    def toggle_omit(self, info, obj):
        for sg in obj.selected_subgroup:
            sg.set_temp_status('ok' if sg.temp_selected else 'omit')


def gchange(obj, gs):
    for g in gs[1:]:
        g.set_preferred_kind(obj.attr, obj.kind, obj.error_kind)


class GroupAgeEditor(BaseTableEditor, ColumnSorterMixin):
    help_str = Str('Right-click to subgroup analyses and calculate an age')
    groups = List
    subgroups = List
    selected_group = List
    selected_subgroup = List
    selected_group_item = Property(depends_on='selected_group')
    selected_subgroup_item = Property(depends_on='selected_subgroup')
    skip_meaning = Str
    unknowns = List

    def make_groups(self, bind=True):
        if bind:
            bind_preference(self, 'skip_meaning', 'pychron.pipeline.skip_meaning')

        sgs = []
        gs = []
        unks = []
        for gid, ans in groupby_group_id(self.items):
            ans = list(ans)
            if self.skip_meaning:
                if 'Human Table' in self.skip_meaning:
                    ans = (ai for ai in ans if ai.tag.lower() != 'skip')

            groups, analyses = make_interpreted_age_groups(ans, group_id=gid)
            sgs.extend(groups)
            unks.extend(groups)
            unks.extend(analyses)

            gs.append(make_interpreted_age_group(groups + analyses, gid))

        self.groups = gs
        self.subgroups = sgs
        self.unknowns = unks

    # action handlers
    def group_selected(self):
        gid = max({a.group_id for a in self.items}) + 1
        for a in self.selected:
            a.group_id = gid

        self.make_groups(False)

    def subgroup_selected(self):
        r = self.selected[0]
        gid = r.group_id

        sgid = max({int(a.subgroup['name']) if a.subgroup else 0 for a in self.items if a.group_id == gid}) + 1
        for a in self.selected:
            a.subgroup = {'name': sgid}

        self.make_groups(False)

    def clear_grouping(self):
        for a in self.selected:
            a.group_id = 0
            a.subgroup = None

        self.make_groups(False)

    # def group_sd(self):
    #     self._group_error(SD)
    #
    # def group_sem(self):
    #     self._group_error(SEM)
    #
    # def group_msem(self):
    #     self._group_error(MSEM)
    #
    # def group(self, kind: object) -> object:
    #     self._group(kind)
    #     self.refresh_needed = True

    # private
    @on_trait_change('selected_subgroup_item:preferred_values:[+]')
    def _group_change(self, obj, name, old, new):
        gchange(obj, self.selected_subgroup)

    @on_trait_change('selected_group_item:preferred_values:[+]')
    def _group_change(self, obj, name, old, new):
        gchange(obj, self.selected_group)

    # def _group_error(self, tag):
    #     if self.selected:
    #         set_subgrouping_error(tag, self.selected, self.items)
    #         self.refresh_needed = True
    #
    # def _group(self, tag):
    #     if self.selected:
    #         d = {'age_kind': tag, 'age_error_kind': MSEM}
    #         apply_subgrouping(d, self.selected, items=self.items)
    #         self.refresh_needed = True

    def _get_selected_group_item(self):
        if self.selected_group:
            ret = self.selected_group[0]
            return ret

    def _get_selected_subgroup_item(self):
        if self.selected_subgroup:
            ret = self.selected_subgroup[0]
            return ret

    def traits_view(self):
        agrp = VGroup(
            # HGroup(UItem('help_str', style='readonly'),
            #        show_border=True, label='Info'),

            UItem('items',
                  editor=myTabularEditor(adapter=AnalysesAdapter(),
                                         # col_widths='col_widths',
                                         selected='selected',
                                         multi_select=True,
                                         auto_update=False,
                                         refresh='refresh_needed',
                                         operations=['delete', 'move'],
                                         column_clicked='column_clicked')),
            label='Analyses',
            show_border=True)

        sgrp = VGroup(UItem('subgroups',
                            height=-100,
                            editor=myTabularEditor(adapter=SubGroupAdapter(),
                                                   multi_select=True,
                                                   editable=False,
                                                   auto_update=True,
                                                   selected='selected_subgroup')),
                      UItem('selected_subgroup_item',
                            style='custom', editor=InstanceEditor(view=View(get_preferred_grp()))),
                      label='SubGroups',
                      show_border=True)

        ggrp = VGroup(UItem('groups',
                            height=-100,
                            style='custom', editor=myTabularEditor(adapter=GroupAdapter(),
                                                                   multi_select=True,
                                                                   editable=False,
                                                                   selected='selected_group')),
                      UItem('selected_group_item',
                            style='custom', editor=InstanceEditor(view=View(get_preferred_grp()))),
                      label='Groups',
                      show_border=True)

        v = View(VGroup(agrp, sgrp, ggrp),

                 handler=THandler())
        return v

# ============= EOF =============================================
