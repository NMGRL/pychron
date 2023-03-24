# ===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.action.menu_manager import MenuManager

from traits.api import Str, Instance, Any, Button
from traitsui.api import InstanceEditor, Controller
from traitsui.api import (
    View,
    UItem,
    VGroup,
    EnumEditor,
    HGroup,
    CheckListEditor,
    spring,
    Group,
    HSplit,
    Tabbed,
    Item,
    VSplit,
)
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.browser.adapters import (
    ProjectAdapter,
    PrincipalInvestigatorAdapter,
    LoadAdapter,
)
from pychron.envisage.browser.pane_model_view import PaneModelView
from pychron.envisage.icon_button_editor import icon_button_editor


class InstanceUItem(UItem):
    """Convenience class for including an Instance in a View"""

    style = Str("custom")
    editor = Instance(InstanceEditor, ())


class GroupView(Controller):
    pane = Any
    controller = Any

    def trait_context(self):
        """Returns the default context to use for editing or configuring
        traits.
        """
        return {
            "object": self.model,
            "controller": self.controller,
            "handler": self.controller,
            "pane": self.pane,
            "table": self.model.table,
        }
        return ctx


class AnalysisGroupsAdapter(TabularAdapter):
    columns = [("Set", "name"), ("Date", "create_date")]

    font = "Arial 10"

    def get_menu(self, obj, trait, row, column):
        actions = [Action(name="Delete", action="delete_analysis_group")]

        return MenuManager(*actions)


irrad_grp = BorderVGroup(
    HGroup(
        UItem("irradiation_enabled", tooltip="Enable Irradiation filter"),
        UItem(
            "irradiation",
            enabled_when="irradiation_enabled",
            editor=EnumEditor(name="irradiations"),
        ),
    ),
    UItem(
        "level", enabled_when="irradiation_enabled", editor=EnumEditor(name="levels")
    ),
    visible_when="irradiation_visible",
    label="Irradiations",
)

project_grp = BorderVGroup(
    UItem(
        "projects",
        editor=FilterTabularEditor(
            editable=False,
            enabled_cb="project_enabled",
            use_fuzzy=True,
            column_index=-1,
            stretch_last_section=False,
            refresh="refresh_needed",
            selected="selected_projects",
            adapter=ProjectAdapter(),
            multi_select=True,
        ),
    ),
    springy=False,
    visible_when="project_visible",
    label="Projects",
)

simple_analysis_type_grp = BorderHGroup(
    UItem("use_analysis_type_filtering", tooltip="Enable Analysis Type filter"),
    icon_button_editor(
        "controller.configure_analysis_type_filter_button",
        "cog",
        tooltip="Configure analysis type filtering",
        enabled_when="use_analysis_type_filtering",
    ),
    label="Analysis Types",
)
simple_date_grp = BorderHGroup(
    UItem("date_enabled", tooltip="Enable Date Filtering"),
    icon_button_editor(
        "controller.configure_date_filter_button",
        "cog",
        enabled_when="date_enabled",
        tooltip="Configure date filtering",
    ),
    label="Date",
)
simple_mass_spectrometer_grp = BorderHGroup(
    UItem("mass_spectrometers_enabled", tooltip="Enable Mass Spectrometer filter"),
    icon_button_editor(
        "controller.configure_mass_spectrometer_filter_button",
        "cog",
        tooltip="Configure mass_spectrometer filtering",
    ),
    label="Mass Spectrometer",
)

pi_grp = Group(
    UItem(
        "principal_investigators",
        height=-75,
        editor=FilterTabularEditor(
            editable=False,
            use_fuzzy=True,
            stretch_last_section=False,
            enabled_cb="principal_investigator_enabled",
            refresh="refresh_needed",
            selected="selected_principal_investigators",
            adapter=PrincipalInvestigatorAdapter(),
            multi_select=True,
        ),
    ),
    springy=False,
    visible_when="principal_investigator_visible",
    show_border=True,
    label="PI",
)

load_grp = BorderVGroup(
    UItem(
        "loads",
        editor=FilterTabularEditor(
            editable=False,
            use_fuzzy=True,
            enabled_cb="load_enabled",
            refresh="refresh_needed",
            selected="selected_loads",
            adapter=LoadAdapter(),
            multi_select=True,
        ),
    ),
    label="Load",
)

search_grp = BorderHGroup(
    UItem(
        "fuzzy_search_entry",
        # tooltip="Enter a simple search, Pychron will do the "
        # "rest. Must enter at least 3 characters. \n\nSome example searches.\n\n"
        # "foo => Find all samples with `foo` in the name, find all projects that start with `foo`\n"
        # "a-1234 => Find all analyses with aliquot = 1234\n"
        # "e776519e-60 => Find the analysis with a UUID that starts with e776519e-60",
    ),
    UItem("fuzzy_search_type"),
    icon_button_editor(
        "execute_fuzzy_search",
        "eye",
        tooltip="Execute Fuzzy Search",
        enabled_when="len(fuzzy_search_entry)>2",
    ),
    label="Search",
)

sample_tools = HGroup(
    UItem(
        "sample_filter_parameter",
        width=-90,
        editor=EnumEditor(name="sample_filter_parameters"),
    ),
    UItem("sample_filter_comparator"),
    UItem("sample_filter", editor=ComboboxEditor(name="sample_filter_values")),
    icon_button_editor("clear_sample_table", "clear", tooltip="Clear Sample Table"),
)

analysis_grp_table = UItem(
    "analysis_groups",
    editor=myTabularEditor(
        adapter=AnalysisGroupsAdapter(),
        multi_select=True,
        editable=False,
        selected="selected_analysis_groups",
    ),
)


class SampleGroupView(GroupView):
    def traits_view(self):
        top_level_filter_grp = VGroup(
            HGroup(
                search_grp,
                simple_mass_spectrometer_grp,
                simple_analysis_type_grp,
                simple_date_grp,
            ),
            HGroup(VGroup(pi_grp, project_grp), VGroup(irrad_grp, load_grp)),
        )

        sample_table = BorderVGroup(
            sample_tools,
            UItem(
                "samples",
                editor=myTabularEditor(
                    adapter=self.model.labnumber_tabular_adapter,
                    editable=False,
                    selected="selected_samples",
                    multi_select=True,
                    dclicked="dclicked_sample",
                    column_clicked="column_clicked",
                    stretch_last_section=False,
                ),
            ),
            label="Samples",
        )
        grp = VGroup(top_level_filter_grp, Tabbed(sample_table, analysis_grp_table))
        return View(grp)


class AnalysisGroupView(GroupView):
    def traits_view(self):
        analysis_tools = VGroup(
            HGroup(
                UItem(
                    "table.analysis_set",
                    width=250,
                    editor=EnumEditor(name="table.analysis_set_names"),
                ),
                icon_button_editor(
                    "table.refresh_analysis_set_button",
                    "refresh",
                    enabled_when="table.items",
                    tooltip="Reload selected analysis set",
                ),
                icon_button_editor(
                    "table.add_analysis_set_button",
                    "add",
                    enabled_when="table.items",
                    tooltip="Add current analyses to an analysis set",
                ),
                icon_button_editor(
                    "add_analysis_group_button",
                    "database_add",
                    enabled_when="table.items",
                    tooltip="Add current analyses to an analysis group",
                ),
            ),
            HGroup(
                UItem(
                    "table.analysis_filter_parameter",
                    width=-90,
                    editor=EnumEditor(name="table.analysis_filter_parameters"),
                ),
                UItem("table.analysis_filter"),
                icon_button_editor(
                    "table.scroll_to_bottom", "arrow_down", tooltip="Scroll to bottom"
                ),
                icon_button_editor(
                    "table.scroll_to_top", "arrow_up", tooltip="Scroll to top"
                ),
                Item("use_quick_recall", label="Quick Recall"),
            ),
        )

        agrp = Group(
            VGroup(
                analysis_tools,
                UItem(
                    "table.analyses",
                    # width=0.75,
                    editor=myTabularEditor(
                        adapter=self.model.table.tabular_adapter,
                        operations=["move", "delete"],
                        column_clicked="table.column_clicked",
                        refresh="table.refresh_needed",
                        selected="table.selected",
                        dclicked="table.dclicked",
                        multi_select=self.pane.multi_select,
                        scroll_to_row="table.scroll_to_row",
                        scroll_to_bottom="table.scroll_to_bottom",
                        scroll_to_top="table.scroll_to_top",
                        stretch_last_section=False,
                    ),
                    visible_when="not use_quick_recall",
                ),
                VSplit(
                    UItem(
                        "table.analyses",
                        height=0.75,
                        editor=myTabularEditor(
                            adapter=self.model.table.tabular_adapter,
                            operations=["move", "delete"],
                            column_clicked="table.column_clicked",
                            refresh="table.refresh_needed",
                            selected="table.selected",
                            dclicked="table.dclicked",
                            key_pressed="table.key_pressed",
                            multi_select=self.pane.multi_select,
                            scroll_to_row="table.scroll_to_row",
                            scroll_to_bottom="table.scroll_to_bottom",
                            scroll_to_top="table.scroll_to_top",
                            stretch_last_section=False,
                        ),
                    ),
                    UItem(
                        "recall_editor",
                        height=0.25,
                        style="custom",
                        visible_when="recall_editor",
                    ),
                    visible_when="use_quick_recall",
                ),
                defined_when=self.pane.analyses_defined,
                show_border=True,
                label="Analyses",
            )
        )
        return View(agrp)


class BaseBrowserSampleView(PaneModelView):
    configure_date_filter_button = Button
    configure_analysis_type_filter_button = Button
    configure_mass_spectrometer_filter_button = Button

    sample_grp = Instance(SampleGroupView)
    selection_grp = Instance(GroupView)

    def _selection_grp_default(self):
        return self._selection_view_klass(
            model=self.model, pane=self.pane, controller=self
        )

    def _sample_grp_default(self):
        s = SampleGroupView(model=self.model, pane=self.pane, controller=self)
        return s

    def traits_view(self):
        return View(
            HSplit(
                InstanceUItem("controller.sample_grp", width=0.5),
                InstanceUItem("controller.selection_grp", width=0.5),
            )
        )

    def _configure_date_filter_button_fired(self):
        grp = BorderHGroup(
            UItem("use_low_post"),
            UItem("low_post", style="custom", enabled_when="use_low_post"),
            UItem("use_high_post"),
            UItem("high_post", style="custom", enabled_when="use_high_post"),
            UItem("use_named_date_range"),
            UItem("named_date_range"),
            label="Date",
            visible_when="date_visible",
        )

        v = okcancel_view(grp, height=150, title="Configure Date Filter")
        info = self.edit_traits(view=v)
        if info.result:
            self.model.refresh_samples()

    def _configure_analysis_type_filter_button_fired(self):
        grp = BorderHGroup(
            UItem(
                "use_analysis_type_filtering",
                tooltip="Enable Analysis Type filter",
                label="Enabled",
            ),
            spring,
            UItem(
                "_analysis_include_types",
                enabled_when="use_analysis_type_filtering",
                style="custom",
                editor=CheckListEditor(cols=5, name="available_analysis_types"),
            ),
            visible_when="analysis_types_visible",
            label="Analysis Types",
        )
        v = okcancel_view(grp, height=150, title="Configure Analysis Type Filter")
        info = self.edit_traits(view=v)
        if info.result:
            self.model.refresh_samples()

    def _configure_mass_spectrometer_filter_button_fired(self):
        grp = BorderHGroup(
            UItem(
                "mass_spectrometers_enabled", tooltip="Enable Mass Spectrometer filter"
            ),
            spring,
            UItem(
                "mass_spectrometer_includes",
                style="custom",
                enabled_when="use_mass_spectrometers",
                editor=CheckListEditor(name="available_mass_spectrometers", cols=10),
            ),
            visible_when="mass_spectrometer_visible",
            label="Mass Spectrometer",
        )

        v = okcancel_view(grp, height=150, title="Configure Mass Spectrometer Filter")
        info = self.edit_traits(view=v)
        if info.result:
            self.model.refresh_samples()


class BrowserSampleView(BaseBrowserSampleView):
    _selection_view_klass = AnalysisGroupView

    # analysis_grp = Instance(AnalysisGroupView)
    #
    # def _analysis_grp_default(self):
    #     a = AnalysisGroupView(model=self.model,
    #                           pane=self.pane,
    #                           controller=self)
    #     return a

    def unselect_projects(self, info, obj):
        obj.selected_projects = []

    def unselect_analyses(self, info, obj):
        obj.selected = []

    def configure_sample_table(self, info, obj):
        obj.configure_sample_table()

    def configure_analysis_table(self, info, obj):
        obj.configure_table()

    def recall_items(self, info, obj):
        obj.context_menu_event = ("open", {"open_copy": False})

    def review_status_details(self, info, obj):
        obj.review_status_details()

    def clear_grouping(self, info, obj):
        obj.clear_grouping()

    def group_selected(self, info, obj):
        obj.group_selected()

    def remove_others(self, info, obj):
        obj.remove_others()

    def clear_selection(self, info, obj):
        obj.clear_selection()

    def toggle_freeze(self, info, obj):
        obj.toggle_freeze()

    def select_same_attr(self, info, obj):
        obj.select_same_attr()

    def select_same(self, info, obj):
        obj.select_same()

    def load_review_status(self, info, obj):
        obj.load_review_status()

    def load_chrono_view(self, info, obj):
        obj.load_chrono_view()

    def delete_analysis_group(self, info, obj):
        obj.delete_analysis_group()

    def tag_ok(self, info, obj):
        self._set_tags(info.object, "ok")

    def tag_omit(self, info, obj):
        self._set_tags(info.object, "omit")

    def tag_invalid(self, info, obj):
        self._set_tags(info.object, "invalid")

    def tag_skip(self, info, obj):
        self._set_tags(info.object, "skip")

    def _set_tags(self, obj, tag):
        items = obj.set_tags(tag)
        if items:
            obj.table.set_tags(tag, items)
            obj.table.remove_invalid()
            obj.table.refresh_needed = True


class InterpretedGroupView(GroupView):
    # def trait_context(self):
    #     # ctx = super(BrowserInterpretedAgeView, self).trait_context()
    #     ctx['table'] = self.model.table
    #     ctx = {'object': self.model, 'controller': self.controller,
    #      'handler': self.controller, 'pane': self.pane, 'table': self.model.table}
    #     return ctx

    def traits_view(self):
        grp = VGroup(
            UItem(
                "table.interpreted_ages",
                editor=myTabularEditor(
                    auto_resize=True,
                    adapter=self.model.table.tabular_adapter,
                    operations=["move", "delete"],
                    selected="table.selected",
                    dclicked="table.dclicked",
                    multi_select=True,
                    stretch_last_section=False,
                ),
            ),
            show_border=True,
            label="Interpreted Ages",
        )

        return View(grp)


class BrowserInterpretedAgeView(BaseBrowserSampleView):
    _selection_view_klass = InterpretedGroupView

    # interpreted_grp = Instance(InterpretedGroupView)
    #
    # def _interpretd_grp_default(self):
    #     a = InterpretedGroupView(model=self.model,
    #                              pane=self.pane,
    #                              controller=self)
    #     return a

    def delete(self, info, obj):
        obj.delete()


# ============= EOF =============================================
