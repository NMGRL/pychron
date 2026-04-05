# ===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import (
    View,
    UItem,
    InstanceEditor,
    TableEditor,
    ObjectColumn,
    HGroup,
    VGroup,
    Item,
    UReadonly,
    TabularEditor,
    TextEditor,
)

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter

from pychron.envisage.icon_button_editor import icon_button_editor


class LibraryEntryAdapter(TabularAdapter):
    """Adapter for displaying library entries in a table."""

    columns = [
        ("Name", "name"),
        ("Class", "class_name"),
        ("Company", "company"),
        ("Status", "is_complete"),
    ]

    is_complete_text = property(lambda self: "Complete" if self.item.is_complete else "Incomplete")
    is_complete_alignment = "center"


class CurrentDevicePane(TraitsTaskPane):
    id = "hardware.current_device"

    def traits_view(self):
        v = View(
            UItem(
                "selected",
                style="custom",
                editor=InstanceEditor(view="current_state_view"),
            )
        )
        return v


class ResponseAdapter(TabularAdapter):
    columns = [("Command", "command"), ("Response", "response")]


class TerminalPane(TraitsDockPane):
    id = "hardware.terminal"
    name = "Terminal"

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(
                    UItem("command"),
                    icon_button_editor(
                        "send_command_button",
                        "arrow_right",
                        tooltip="Send command to device",
                        enabled_when="command",
                    ),
                ),
                UItem("responses", editor=TabularEditor(adapter=ResponseAdapter())),
            )
        )
        return v


class ConfigurationPane(TraitsDockPane):
    id = "hardware.configuration"
    name = "Configuration"

    def trait_context(self):
        if self.model:
            return {
                "object": self.model.device_configurer,
                "scan": self.model.device_configurer.scan_grp,
                "pane": self,
            }
        return super(TraitsDockPane, self).trait_context()

    def traits_view(self):
        comms_grp = VGroup(
            UItem("communication_grp", style="custom"),
            visible_when="comms_visible",
            show_border=True,
            label="Communications",
        )

        scan_grp = VGroup(
            Item("scan.enabled"),
            VGroup(
                Item("scan.graph"),
                Item("scan.record"),
                Item("scan.auto_start"),
                Item("scan.period"),
                enabled_when="scan.enabled",
            ),
            UItem("save_button"),
            show_border=True,
            label="Scan",
        )

        v = View(
            VGroup(
                HGroup(
                    UReadonly("config_name"),
                    icon_button_editor("save_button", "document-save", enabled_when="config_path"),
                ),
                comms_grp,
                scan_grp,
            ),
            height=500,
            resizable=True,
        )
        return v


class InfoPane(TraitsDockPane):
    id = "hardware.info"
    name = "Current Device"

    def traits_view(self):
        v = View(UItem("selected", style="custom", editor=InstanceEditor(view="info_view")))
        return v


class DevicesPane(TraitsDockPane):
    id = "hardware.devices"
    name = "Devices"

    def traits_view(self):
        cols = [
            ObjectColumn(name="name"),
            ObjectColumn(name="connected"),
            ObjectColumn(name="com_class", label="Com. Class"),
            ObjectColumn(name="klass", label="Class"),
        ]
        table_editor = TableEditor(
            columns=cols, editable=False, selected="selected", selection_mode="row"
        )
        v = View(UItem("devices", editor=table_editor))
        return v


class LibraryPane(TraitsDockPane):
    """Pane for displaying hardware device library and generating configs."""

    id = "hardware.library"
    name = "Device Library"

    def traits_view(self):
        # Phase 2.2: Search and filter controls
        search_group = VGroup(
            UItem("library_filter", editor=InstanceEditor(), style="custom"),
            show_border=True,
            label="Search & Filter",
        )

        # Library table showing filtered entries (Phase 2.2)
        library_table = TabularEditor(
            adapter=LibraryEntryAdapter(),
            selected="library_selected",
        )

        # Statistics display (Phase 2.2)
        stats_group = Item("library_stats", label="", style="readonly", show_label=False)

        # Phase 3.1: Template management
        template_group = VGroup(
            Item("selected_template_name", editor=TextEditor(), label="Select Template"),
            HGroup(
                icon_button_editor(
                    "load_template_button",
                    "arrow-down",
                    tooltip="Load template",
                    enabled_when="selected_template_name",
                ),
                icon_button_editor(
                    "manage_templates_button",
                    "document",
                    tooltip="Manage templates",
                ),
            ),
            Item("template_name_input", label="New Template Name"),
            Item("template_description_input", label="Description"),
            HGroup(
                icon_button_editor(
                    "save_as_template_button",
                    "document-save",
                    tooltip="Save as template",
                    enabled_when="template_name_input",
                ),
            ),
            show_border=True,
            label="Templates",
        )

        v = View(
            VGroup(
                search_group,
                stats_group,
                UItem("filtered_library_entries", editor=library_table, height=200),
                template_group,
            ),
            height=600,
            resizable=True,
        )
        return v


# ============= EOF =============================================
