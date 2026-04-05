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

import os

from traits.api import (
    HasTraits,
    Button,
    Instance,
    List,
    Str,
    Enum,
    Int,
    Float,
    Event,
    Property,
    cached_property,
)
from traits.trait_types import Bool
from traitsui.api import View, Item, VGroup

from pychron.config_mixin import ParserWrapper
from pychron.core.helpers.filetools import backup
from pychron.core.pychron_traits import IPAddress
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.hardware.library import LibraryEntry
from pychron.hardware.library_filter import LibraryFilter, LibrarySearcher
from pychron.hardware.config_template import ConfigTemplate
from pychron.hardware.config_template_manager import ConfigTemplateManager
from pychron.hardware.config_import_export import (
    ConfigExporter,
    ConfigImporter,
)
from pychron.hardware.validation_reporter import MetadataValidator
from pychron.hardware.metadata_editor import MetadataEditor
from pychron.hardware.driver_generator import DriverWizard


# ============= standard library imports ========================
# ============= local library imports  ==========================


class ConfigGroup(HasTraits):
    config_obj = None

    def _anytrait_changed(self, name, new):
        """
        update the config object with the current user value
        """
        if self.config_obj:
            if self.config_obj.has_option(self.tag, name):
                self.config_obj.set(self.tag, name, new)


class ScanGroup(ConfigGroup):
    tag = "Scan"
    enabled = Bool
    graph = Bool
    record = Bool
    auto_start = Bool
    period = Float


class CommunicationGroup(ConfigGroup):
    tag = "Communications"


class SerialCommunicationGroup(CommunicationGroup):
    port = Str
    baudrate = Enum(300, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200, 230400)

    def load_from_config(self, cfg):
        self.port = cfg("port")
        self.baudrate = cfg("baudrate", cast="int")

    def traits_view(self):
        v = View(VGroup(Item("port"), Item("baudrate")))
        return v


class EthernetCommunicationGroup(CommunicationGroup):
    host = IPAddress
    port = Int
    kind = Enum("TCP", "UDP")

    def load_from_config(self, cfg):
        self.port = cfg("port", cast="int")
        self.host = cfg("host", default="localhost")
        self.kind = cfg("kind", default="UDP")

    def traits_view(self):
        v = View(Item("host"), Item("port"), Item("kind"))
        return v


CKLASS_DICT = {
    "ethernet": EthernetCommunicationGroup,
    "serial": SerialCommunicationGroup,
}


class DeviceConfigurer(Loggable):
    config_path = Str
    config_name = Str
    save_button = Button
    _config = None

    kind = Enum("ethernet", "serial")
    communication_grp = Instance(CommunicationGroup)
    scan_grp = Instance(ScanGroup, ())
    comms_visible = Bool(False)

    def set_device(self, device):
        p = device.config_path
        self._load_configuration(p)

    def _load_configuration(self, path):
        self.config_path = path
        self.config_name = os.path.relpath(path, paths.device_dir)
        # self._config = cfg = six.moves.configparser.ConfigParser()
        self._config = cfg = ParserWrapper()
        cfg.read(path)

        section = "Communications"
        if cfg.has_section(section):
            if cfg.has_option(section, "type"):
                kind = cfg.get(section, "type")
                klass = CKLASS_DICT.get(kind)
                if klass:
                    self.communication_grp = klass()

                    def func(option, cast=None, default=None, **kw):
                        f = getattr(cfg, "get{}".format(cast if cast else ""))
                        if cfg.has_option(section, option):
                            v = f(section, option, **kw)
                        else:
                            v = default
                            if v is None:
                                if cast == "boolean":
                                    v = False
                                elif cast in ("float", "int"):
                                    v = 0
                        return v

                    self.communication_grp.load_from_config(func)
                    self.communication_grp.config_obj = cfg
                    self.comms_visible = True
        else:
            self.comms_visible = False
            self.communication_grp = CommunicationGroup()

        section = "Scan"
        if cfg.has_section(section):
            bfunc = lambda *args: cfg.getboolean(*args)
            ffunc = lambda *args: cfg.getfloat(*args)
        else:
            bfunc = lambda *args: False
            ffunc = lambda *args: 0

        sgrp = self.scan_grp
        for attr in ("enabled", "graph", "record", "auto_start"):
            if cfg.has_option(section, attr):
                v = bfunc(section, attr)
            else:
                v = False
            setattr(sgrp, attr, v)

        for attr in ("period",):
            if cfg.has_option(section, attr):
                v = ffunc(section, attr)
            else:
                v = 0
            setattr(sgrp, attr, v)

    def _save_button_fired(self):
        self._dump()

    def _dump(self):
        # backup previous file
        # putting the device dir under git control is a good idea

        self._backup()
        with open(self.config_path, "w") as wfile:
            self._config.write(wfile)

    def _backup(self):
        bp, pp = backup(self.config_path, paths.backup_device_dir, extension=".cfg")
        self.info("{} - saving a backup copy to {}".format(bp, pp))


class CommandResponse(HasTraits):
    command = Str
    response = Str


class Hardwarer(Loggable):
    devices = List
    selected = Instance(ICoreDevice)
    device_configurer = Instance(DeviceConfigurer, ())

    command = Str
    responses = List
    send_command_button = Button

    # Library management
    library_entries = List(LibraryEntry)
    library_selected = Instance(LibraryEntry)
    generate_config_button = Button
    generate_config_comm_type = Enum("ethernet", "serial")
    generate_config_device_name = Str
    generate_config_allow_overwrite = Bool(False)
    config_generated = Event

    # Library filtering (Phase 2.2)
    library_filter = Instance(LibraryFilter, ())
    filtered_library_entries = Property(List(LibraryEntry), observe="library_entries")
    available_companies = Property(List(Str), observe="library_entries")
    available_comm_types = Property(List(Str), observe="library_entries")
    library_stats = Property(Str, observe="filtered_library_entries")

    # Link opening (Phase 2.1)
    open_docs_button = Button
    open_website_button = Button

    # Template management (Phase 3.1)
    template_manager = Instance(ConfigTemplateManager)
    available_templates = Property(List(Str))
    selected_template_name = Str
    save_as_template_button = Button
    load_template_button = Button
    manage_templates_button = Button
    template_name_input = Str
    template_description_input = Str

    # Import/Export (Phase 3.2)
    export_configs_button = Button
    import_configs_button = Button
    export_path = Str
    import_path = Str

    # Validation Dashboard (Phase 4.1)
    validation_report_button = Button
    export_report_button = Button
    validation_report_text = Str
    validation_completeness = Property(Str, observe="library_entries")

    # Metadata Editor (Phase 4.2)
    metadata_editor = Instance(MetadataEditor)
    edit_metadata_button = Button
    metadata_edit_status = Str

    # Driver Wizard (Phase 4.3)
    driver_wizard_button = Button
    driver_output_dir = Str

    def __init__(self, *args, **kwargs):
        super(Hardwarer, self).__init__(*args, **kwargs)
        self.template_manager = ConfigTemplateManager()
        self.template_manager.load_templates()
        self.metadata_editor = MetadataEditor()
        self._load_library()

    def _load_library(self):
        """Load and cache hardware library entries."""
        try:
            from pychron.hardware.library import get_library_entries

            self.library_entries = get_library_entries()
            self.debug(f"Loaded {len(self.library_entries)} hardware library entries")
        except Exception as e:
            self.warning(f"Failed to load hardware library: {e}")

    def _get_filtered_library_entries(self):
        """Get filtered library entries based on current filter criteria."""
        return LibrarySearcher.filter_entries(self.library_entries, self.library_filter)

    def _get_available_companies(self):
        """Get list of unique companies from library entries."""
        return LibrarySearcher.get_unique_companies(self.library_entries)

    def _get_available_comm_types(self):
        """Get list of unique communication types from library entries."""
        return LibrarySearcher.get_unique_comm_types(self.library_entries)

    def _get_library_stats(self):
        """Get formatted statistics string for filtered entries."""
        filtered = self.filtered_library_entries
        if not filtered:
            return "No devices match filters"

        total, complete, percentage = LibrarySearcher.get_completeness_stats(filtered)
        return (
            f"Showing {len(filtered)} of {len(self.library_entries)} devices "
            f"({complete}/{len(filtered)} complete, {percentage:.0f}%)"
        )

    def _send_command_button_fired(self):
        if self.selected:
            c = CommandResponse(command=self.command)
            self.responses.insert(0, c)
            resp = self.selected.ask(self.command)
            if resp is not None:
                c.response = resp

    def _generate_config_button_fired(self):
        """Generate config file for selected library entry."""
        if not self.library_selected:
            self.warning("No library entry selected")
            return

        if not self.library_selected.is_complete:
            self.warning(f"Cannot generate config: {self.library_selected.missing_fields}")
            return

        device_name = self.generate_config_device_name or self.library_selected.name

        try:
            from pychron.hardware.library import generate_device_config

            result = generate_device_config(
                self.library_selected,
                device_name,
                comm_type=self.generate_config_comm_type,
                allow_overwrite=self.generate_config_allow_overwrite,
            )

            if result.success:
                self.info(str(result))
                self.config_generated = True
            else:
                self.warning(f"Config generation failed: {result.error}")
        except Exception as e:
            self.exception(f"Error generating config: {e}")

    def _open_docs_button_fired(self):
        """Open documentation URL in web browser (Phase 2.1)."""
        if self.library_selected and self.library_selected.docs_url:
            self._open_url(self.library_selected.docs_url, "Documentation")

    def _open_website_button_fired(self):
        """Open company website in web browser (Phase 2.1)."""
        if self.library_selected and self.library_selected.website:
            self._open_url(self.library_selected.website, "Website")

    def _open_url(self, url: str, url_type: str) -> None:
        """
        Open URL in default web browser.

        Args:
            url: URL to open
            url_type: Type of URL (for logging)
        """
        try:
            import webbrowser

            webbrowser.open(url)
            self.info(f"Opened {url_type}: {url}")
        except Exception as e:
            self.warning(f"Failed to open {url_type}: {e}")

    def _get_available_templates(self):
        """Get list of template names for display."""
        return sorted(self.template_manager.templates.keys())

    def _save_as_template_button_fired(self):
        """Save current device configuration as a template."""
        if not self.library_selected:
            self.warning("No library entry selected")
            return

        if not self.template_name_input.strip():
            self.warning("Template name cannot be empty")
            return

        try:
            template = ConfigTemplate(
                name=self.template_name_input,
                device_class=self.library_selected.class_name,
                comm_type=self.library_selected.default_comm_type,
                settings={},  # Will be populated from device config
                description=self.template_description_input,
            )

            if self.template_manager.save_template(template):
                self.info(f"Saved template: {template.name}")
                self.template_name_input = ""
                self.template_description_input = ""
            else:
                self.warning(f"Failed to save template: {template.name}")
        except Exception as e:
            self.exception(f"Error saving template: {e}")

    def _load_template_button_fired(self):
        """Load configuration from selected template."""
        if not self.selected_template_name:
            self.warning("No template selected")
            return

        try:
            template = self.template_manager.get_template(self.selected_template_name)
            if template:
                self.info(f"Loaded template: {template.name}")
                # Template loading implementation would integrate with device config
            else:
                self.warning(f"Template not found: {self.selected_template_name}")
        except Exception as e:
            self.exception(f"Error loading template: {e}")

    def _manage_templates_button_fired(self):
        """Open template management dialog."""
        try:
            stats = self.template_manager.get_statistics()
            self.info(
                f"Templates: {stats['total_templates']} total, "
                f"{stats['device_classes']} device classes, "
                f"{stats['comm_types']} comm types"
            )
        except Exception as e:
            self.exception(f"Error getting template stats: {e}")

    def _export_configs_button_fired(self):
        """Export selected device configs to ZIP bundle."""
        if not self.library_selected:
            self.warning("No library entry selected")
            return

        try:
            from pathlib import Path

            if not self.export_path:
                self.warning("Export path not specified")
                return

            output_path = Path(self.export_path)
            result = ConfigExporter.export_device_configs([self.library_selected], output_path)

            if result.success:
                self.info(f"Exported {result.exported_count} config(s) to {result.output_path}")
            else:
                self.warning(f"Export failed: {result.error}")

        except Exception as e:
            self.exception(f"Error exporting configs: {e}")

    def _import_configs_button_fired(self):
        """Import device configs from ZIP bundle."""
        if not self.import_path:
            self.warning("Import path not specified")
            return

        try:
            from pathlib import Path

            bundle_path = Path(self.import_path)
            output_dir = paths.device_dir

            result = ConfigImporter.import_device_configs(bundle_path, output_dir)

            if result.success:
                self.info(f"Imported {result.imported_count} config(s) from {bundle_path}")
            else:
                self.warning(f"Import failed: {result.errors}")

        except Exception as e:
            self.exception(f"Error importing configs: {e}")

    def _get_validation_completeness(self):
        """Get validation completeness metric."""
        try:
            report = MetadataValidator.generate_report(self.library_entries)
            return f"{report.completion_percentage:.1f}% complete"
        except Exception:
            return "N/A"

    def _validation_report_button_fired(self):
        """Generate and display metadata validation report."""
        try:
            report = MetadataValidator.generate_report(self.library_entries)

            # Create summary text
            summary_lines = [
                f"Validation Report: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Entries: {report.total_entries}",
                f"Complete: {report.complete_entries}",
                f"Incomplete: {report.incomplete_entries}",
                f"Completion: {report.completion_percentage:.1f}%",
                "",
                "Suggestions:",
            ]

            suggestions = MetadataValidator.suggest_improvements(report)
            for suggestion in suggestions:
                summary_lines.append(f"- {suggestion}")

            self.validation_report_text = "\n".join(summary_lines)
            self.info(f"Validation report generated: {report.completion_percentage:.1f}% complete")

        except Exception as e:
            self.exception(f"Error generating validation report: {e}")

    def _export_report_button_fired(self):
        """Export validation report to file."""
        try:
            report = MetadataValidator.generate_report(self.library_entries)

            output_path = paths.device_dir / "validation_report"
            if MetadataValidator.export_report(report, output_path, format="html"):
                self.info(f"Report exported to {output_path}.html")
            else:
                self.warning("Failed to export validation report")

        except Exception as e:
            self.exception(f"Error exporting report: {e}")

    def _edit_metadata_button_fired(self):
        """Open metadata editor for selected entry."""
        if not self.library_selected:
            self.warning("No library entry selected")
            return

        try:
            session = self.metadata_editor.begin_edit(self.library_selected)
            self.metadata_edit_status = f"Editing: {self.library_selected.name}"
            self.info(f"Started editing metadata for {self.library_selected.name}")

        except Exception as e:
            self.exception(f"Error starting metadata editor: {e}")

    def _driver_wizard_button_fired(self):
        """Open driver creation wizard."""
        try:
            wizard = DriverWizard()
            self.info(
                f"Driver wizard started. Output directory: {self.driver_output_dir or 'default'}"
            )
            # Wizard would be shown in a dialog in real UI implementation

        except Exception as e:
            self.exception(f"Error starting driver wizard: {e}")

    def _selected_changed(self, new):
        if new:
            self.device_configurer.set_device(new)


if __name__ == "__main__":
    from pychron.hardware.tasks.hardware_pane import ConfigurationPane

    dc = DeviceConfigurer()
    p = "/Users/ross/Pychron_dev/setupfiles/devices/bone_micro_ion_controller.cfg"
    p = "/Users/ross/Pychron_dev/setupfiles/devices/apis_controller.cfg"
    dc._load_configuration(p)

    class A(HasTraits):
        device_configurer = dc

    pane = ConfigurationPane(model=A())
    pane.configure_traits()
# ============= EOF =============================================
