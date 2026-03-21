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
from traits.api import Property, Str, Int, List, on_trait_change, Bool
from traitsui.api import (
    View,
    UItem,
    VGroup,
    Handler,
    InstanceEditor,
    Item,
    HGroup,
    spring,
)
from traitsui.menu import Action

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.helpers.color_generators import colornames
from pychron.core.helpers.iterfuncs import groupby_group_id
from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.persistence_loggable import PersistenceMixin
from pychron.pipeline.editors.base_adapter import BaseAdapter
from pychron.pipeline.editors.base_table_editor import BaseTableEditor
from pychron.pipeline.subgrouping import (
    compress_groups,
    make_interpreted_age_groups,
    make_interpreted_age_group,
)
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup
from pychron.processing.analyses.preferred import get_preferred_grp

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class GroupAdapter(BaseAdapter):
    columns = [
        ("Group", "group_id"),
        # ('Name', 'name'),
        ("Age Kind", "age_kind"),
        ("Error", "age_error_kind"),
    ]

    group_id_width = Int(60)
    age_kind_text = Property
    age_error_kind_text = Property

    def _get_age_error_kind_text(self):
        pv = self.item.get_preferred_obj("age")
        return pv.error_kind

    def _get_age_kind_text(self):
        pv = self.item.get_preferred_obj("age")
        return pv.kind


class SubGroupAdapter(GroupAdapter):
    columns = [
        ("Status", "tag"),
        ("Sample", "sample"),
        ("Group", "group_id"),
        ("SubGroup", "subgroup_id"),
        ("Label", "label_name"),
        ("N", "nanalyses"),
        ("Age Kind", "age_kind"),
        ("Error", "age_error_kind"),
    ]

    subgroup_id_width = Int(60)
    tag_width = Int(60)
    tag_text = Property

    def _get_tag_text(self):
        return "Omit" if self.item.is_omitted() else "Include"

    def get_menu(self, obj, trait, row, column):
        m = MenuManager(Action(name="Toggle Omit", action="toggle_omit"))
        return m


class AnalysesAdapter(SubGroupAdapter):
    columns = [
        ("RunID", "record_id"),
        ("Sample", "sample"),
        ("Tag", "tag"),
        ("Group", "group_id"),
        ("SubGroup", "subgroup"),
        ("Age", "age"),
        (PLUSMINUS_ONE_SIGMA, "age_err"),
        ("Exclude Isochron", "exclude_from_isochron"),
    ]

    subgroup_text = Property
    record_id_width = Int(60)
    subgroup_width = Int(100)
    exclude_from_isochron_text = Property

    def get_text_color(self, obj, trait, row, column=0):
        return colornames[self.item.group_id % len(colornames)]

    def _get_exclude_from_isochron_text(self):
        return "Yes" if self.item.exclude_from_isochron else ""

    def _get_tag_text(self):
        return self.item.tag

    def _get_subgroup_text(self):
        return self._get_subgroup_attr("name")

    def _get_subgroup_attr(self, attr):
        ret = ""
        if hasattr(self.item, "subgroup") and self.item.subgroup:
            ret = self.item.subgroup[attr]
        return ret

    def get_menu(self, obj, trait, row, column):
        m = MenuManager(
            Action(name="Clear Grouping", action="clear_grouping"),
            Action(name="Group Selected", action="group_selected"),
            Action(name="SubGroup Selected", action="subgroup_selected"),
            Action(
                name="Toggle Exclude From Isochron",
                action="toggle_exclude_from_isochron",
            ),
        )
        return m


class THandler(Handler):
    def toggle_exclude_from_isochron(self, info, obj):
        obj.toggle_exclude_from_isochron()

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
            sg.set_temp_status("ok" if sg.temp_selected else "omit")


def gchange(obj, gs):
    for g in gs[1:]:
        g.set_preferred_kind(obj.attr, obj.kind, obj.error_kind)


class GroupAgeEditor(BaseTableEditor, ColumnSorterMixin, PersistenceMixin):
    help_str = Str("Right-click to subgroup analyses and calculate an age")
    groups = List
    selected_group = List

    selected_group_item = Property(depends_on="selected_group")
    skip_meaning = Str
    unknowns = List

    arar_calculation_options = None

    # integrated_include_omitted = Bool(False)
    # omit_non_plateau = Bool(False)

    persistence_name = "group_age_editor"
    pattributes = [
        "include_j_position_error",
        "include_j_error_in_mean",
        "include_decay_error_in_mean",
    ]

    include_j_position_error = Bool(False)
    include_j_error_in_mean = Bool(False)
    include_decay_error_in_mean = Bool(False)

    def __init__(self, bind=True, *args, **kw):
        super(GroupAgeEditor, self).__init__(*args, **kw)
        if bind:
            bind_preference(self, "skip_meaning", "pychron.pipeline.skip_meaning")

    def make_groups(self):
        gs = []
        unks = []
        for gid, ans in groupby_group_id(self.items):
            try:
                egroup = self.groups[gid]
            except IndexError:
                egroup = None

            ans = list(ans)
            if self.skip_meaning:
                if "Human Table" in self.skip_meaning:
                    ans = [ai for ai in ans if ai.tag.lower() != "skip"]

            unks.extend(ans)

            ag = InterpretedAgeGroup(analyses=ans, group_id=gid)

            acopt = self.arar_calculation_options
            if acopt:
                ag.integrated_include_omitted = acopt.integrated_include_omitted
                if acopt.isochron_exclude_non_plateau:
                    ag.exclude_non_plateau = acopt.isochron_exclude_non_plateau
                elif acopt.isochron_omit_non_plateau:
                    ag.do_omit_non_plateau()
            else:
                ag.set_external_error(
                    self.include_j_position_error,
                    self.include_j_error_in_mean,
                    self.include_decay_error_in_mean,
                    dirty=True,
                )

            ag.set_preferred_kinds(sg=egroup)

            gs.append(ag)

        self.groups = gs
        self.unknowns = unks
        self.selected_group = gs[:1]

    # action handlers
    def toggle_exclude_from_isochron(self):
        for a in self.selected:
            a.exclude_from_isochron = not a.exclude_from_isochron

        self.make_groups()

    def group_selected(self):
        gid = max({a.group_id for a in self.items}) + 1
        for a in self.selected:
            a.group_id = gid

        self.make_groups()

    def clear_grouping(self):
        for a in self.selected:
            a.group_id = 0
            a.subgroup = None

        self.make_groups()

    # private
    def _include_j_error_in_mean_changed(self):
        for a in self.groups:
            a.set_external_error(
                self.include_j_position_error,
                self.include_j_error_in_mean,
                self.include_decay_error_in_mean,
                dirty=True,
            )
            a.set_preferred_kinds()

    def _subgroup_subgroup_sort_key(self, x):
        if hasattr(x, "subgroup"):
            if x.subgroup:
                return x.subgroup.get("name")

    @on_trait_change("selected_group_item:preferred_values:[+]")
    def _group_change(self, obj, name, old, new):
        gchange(obj, self.selected_group)

    @on_trait_change("selected_group_item:isochron_method")
    def _isochron_method_change(self, obj, name, old, new):
        for gi in self.selected_group[1:]:
            gi.isochron_method = new

    def _get_selected_group_item(self):
        if self.selected_group:
            ret = self.selected_group[0]
            return ret

    def get_analyses_group(self):
        agrp = VGroup(
            # HGroup(UItem('help_str', style='readonly'),
            #        show_border=True, label='Info'),
            UItem(
                "items",
                editor=myTabularEditor(
                    adapter=AnalysesAdapter(),
                    # col_widths='col_widths',
                    selected="selected",
                    multi_select=True,
                    auto_update=False,
                    refresh="refresh_needed",
                    operations=["delete", "move"],
                    column_clicked="column_clicked",
                ),
            ),
            label="Analyses",
            show_border=True,
        )
        return agrp

    def get_groups_group(self):
        ggrp = BorderVGroup(
            UItem(
                "groups",
                height=0.25,
                style="custom",
                editor=myTabularEditor(
                    adapter=GroupAdapter(),
                    multi_select=True,
                    editable=False,
                    selected="selected_group",
                ),
            ),
            UItem(
                "selected_group_item",
                style="custom",
                editor=InstanceEditor(
                    view=View(
                        VGroup(
                            HGroup(
                                BorderHGroup(
                                    Item("fixed_step_low", label="Start"),
                                    Item("fixed_step_high", label="End"),
                                    spring,
                                    label="Calculate Plateau",
                                ),
                                BorderHGroup(
                                    Item("isochron_method", label="Method"),
                                    label="Isochron",
                                ),
                            ),
                            get_preferred_grp(),
                        )
                    )
                ),
            ),
            label="Groups",
        )
        return ggrp

    def get_options_group(self):
        return BorderHGroup(  # Item('include_j_position_error'),
            Item("include_j_error_in_mean"),
            Item("include_decay_error_in_mean"),
            label="Options",
        )

    #     return BorderVGroup(HGroup(BorderVGroup(Item('integrated_include_omitted',
    #                                           tooltip='Include omitted steps in the integrated age',
    #                                           label='Include Omitted'),
    #                                      label='Integrated'),
    #                         BorderVGroup(Item('omit_non_plateau',
    #                                           tooltip='Omit non plateau steps from the isochron age',
    #                                           label='Omit Non Plateau'),
    #                                      label='Isochron')),
    #                         label='Options')

    def traits_view(self):
        agrp = self.get_analyses_group()
        ggrp = self.get_groups_group()
        optsgrp = self.get_options_group()

        v = View(VGroup(optsgrp, agrp, ggrp), handler=THandler())
        return v


class SubGroupAgeEditor(GroupAgeEditor):
    subgroups = List
    selected_subgroup = List
    selected_subgroup_item = Property(depends_on="selected_subgroup")

    def make_groups(self, bind=True):
        if bind:
            bind_preference(self, "skip_meaning", "pychron.pipeline.skip_meaning")

        sgs = []
        gs = []
        unks = []
        for gid, ans in groupby_group_id(self.items):
            ans = list(ans)
            if self.skip_meaning:
                if "Human Table" in self.skip_meaning:
                    ans = (ai for ai in ans if ai.tag.lower() != "skip")

            groups, analyses = make_interpreted_age_groups(ans, group_id=gid)
            sgs.extend(groups)
            unks.extend(groups)
            unks.extend(analyses)

            gs.append(make_interpreted_age_group(groups + analyses, gid))

        self.groups = gs
        self.subgroups = sgs
        self.unknowns = unks

    def subgroup_selected(self):
        r = self.selected[0]
        gid = r.group_id

        sgid = (
            max(
                {
                    int(a.subgroup["name"]) if a.subgroup else 0
                    for a in self.items
                    if a.group_id == gid
                }
            )
            + 1
        )
        for a in self.selected:
            a.subgroup = {"name": sgid}

        self.make_groups()

    @on_trait_change("selected_subgroup_item:preferred_values:[+]")
    def _group_change(self, obj, name, old, new):
        gchange(obj, self.selected_subgroup)

    def _get_selected_subgroup_item(self):
        if self.selected_subgroup:
            ret = self.selected_subgroup[0]
            return ret

    def traits_view(self):
        agrp = self.get_analyses_group()
        ggrp = self.get_groups_group()
        sgrp = VGroup(
            UItem(
                "subgroups",
                height=0.25,
                editor=myTabularEditor(
                    adapter=SubGroupAdapter(),
                    multi_select=True,
                    editable=False,
                    auto_update=True,
                    selected="selected_subgroup",
                ),
            ),
            UItem(
                "selected_subgroup_item",
                style="custom",
                editor=InstanceEditor(view=View(get_preferred_grp())),
            ),
            label="SubGroups",
            show_border=True,
        )

        v = View(VGroup(agrp, sgrp, ggrp), handler=THandler())
        return v


# ============= EOF =============================================
