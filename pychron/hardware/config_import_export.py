"""Configuration import/export functionality for device configs.

This module provides classes for exporting device configurations and templates
as ZIP bundles, and importing them back with validation and conflict resolution.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import zipfile
import json
import logging

from pychron.hardware.library import LibraryEntry
from pychron.hardware.config_template import ConfigTemplate

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of an import operation.

    Attributes:
        success: Whether import succeeded
        imported_count: Number of items successfully imported
        skipped_count: Number of items skipped (conflicts, etc.)
        errors: List of error messages
        timestamp: When import completed
    """

    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    errors: List[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def __str__(self):
        msg = f"Import: {self.imported_count} imported, {self.skipped_count} skipped"
        if self.errors:
            msg += f"\nErrors: {'; '.join(self.errors[:3])}"
        return msg


@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        success: Whether export succeeded
        output_path: Path to exported file
        exported_count: Number of items exported
        file_size: Size of exported file in bytes
        error: Error message if failed
    """

    success: bool
    output_path: Optional[Path] = None
    exported_count: int = 0
    file_size: int = 0
    error: Optional[str] = None


class ConfigExporter:
    """Exporter for device configurations and templates.

    Handles exporting device configs and templates to ZIP bundles for
    sharing and backup purposes.
    """

    @staticmethod
    def export_device_configs(entries: List[LibraryEntry], output_path: Path) -> ExportResult:
        """Export selected device configurations to ZIP.

        Args:
            entries: List of LibraryEntry instances to export
            output_path: Path where ZIP file will be written

        Returns:
            ExportResult with status and details
        """
        if not entries:
            return ExportResult(success=False, error="No entries to export", exported_count=0)

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Write metadata
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "count": len(entries),
                    "type": "device_configs",
                    "entries": [],
                }

                for entry in entries:
                    try:
                        entry_data = {
                            "name": entry.name,
                            "class_name": entry.class_name,
                            "company": entry.company,
                            "model": entry.model,
                            "comm_type": entry.default_comm_type,
                            "metadata": entry.metadata,
                        }
                        metadata["entries"].append(entry_data)

                        # Also write individual metadata as JSON files
                        config_name = f"configs/{entry.name}.json"
                        zf.writestr(config_name, json.dumps(entry_data, indent=2))

                    except Exception as e:
                        logger.error(f"Failed to export entry {entry.name}: {e}")

                # Write main metadata file
                zf.writestr("metadata.json", json.dumps(metadata, indent=2))

            file_size = output_path.stat().st_size
            logger.info(
                f"Exported {len(entries)} device configs to {output_path} " f"({file_size} bytes)"
            )

            return ExportResult(
                success=True,
                output_path=output_path,
                exported_count=len(entries),
                file_size=file_size,
            )

        except Exception as e:
            logger.error(f"Failed to export configs: {e}")
            return ExportResult(success=False, error=str(e), exported_count=0)

    @staticmethod
    def export_templates(templates: List[ConfigTemplate], output_path: Path) -> ExportResult:
        """Export configuration templates to ZIP.

        Args:
            templates: List of ConfigTemplate instances to export
            output_path: Path where ZIP file will be written

        Returns:
            ExportResult with status and details
        """
        if not templates:
            return ExportResult(success=False, error="No templates to export", exported_count=0)

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Write metadata
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "count": len(templates),
                    "type": "templates",
                    "templates": [],
                }

                for template in templates:
                    try:
                        template_data = template.to_dict()
                        metadata["templates"].append(
                            {"name": template.name, "device_class": template.device_class}
                        )

                        # Write individual template as JSON
                        template_name = f"templates/{template.name}.json"
                        zf.writestr(template_name, template.to_json())

                    except Exception as e:
                        logger.error(f"Failed to export template {template.name}: {e}")

                # Write main metadata file
                zf.writestr("metadata.json", json.dumps(metadata, indent=2))

            file_size = output_path.stat().st_size
            logger.info(
                f"Exported {len(templates)} templates to {output_path} " f"({file_size} bytes)"
            )

            return ExportResult(
                success=True,
                output_path=output_path,
                exported_count=len(templates),
                file_size=file_size,
            )

        except Exception as e:
            logger.error(f"Failed to export templates: {e}")
            return ExportResult(success=False, error=str(e), exported_count=0)


class ConfigImporter:
    """Importer for device configurations and templates.

    Handles importing device configs and templates from ZIP bundles with
    validation and conflict resolution.
    """

    @staticmethod
    def validate_config_content(config_content: str) -> bool:
        """Validate configuration file structure.

        Args:
            config_content: INI-format config content

        Returns:
            True if config is valid, False otherwise
        """
        try:
            import configparser

            parser = configparser.ConfigParser()
            parser.read_string(config_content)

            # Check for required sections
            return len(parser.sections()) > 0

        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False

    @staticmethod
    def validate_bundle(bundle_path: Path, bundle_type: str = "any") -> bool:
        """Validate ZIP bundle structure and content.

        Args:
            bundle_path: Path to ZIP bundle
            bundle_type: Type to validate ('device_configs', 'templates', or 'any')

        Returns:
            True if bundle is valid, False otherwise
        """
        if not bundle_path.exists():
            logger.error(f"Bundle not found: {bundle_path}")
            return False

        try:
            with zipfile.ZipFile(bundle_path, "r") as zf:
                # Check for metadata
                if "metadata.json" not in zf.namelist():
                    logger.error("Bundle missing metadata.json")
                    return False

                # Validate metadata
                metadata_str = zf.read("metadata.json").decode("utf-8")
                metadata = json.loads(metadata_str)

                if bundle_type != "any":
                    if metadata.get("type") != bundle_type:
                        logger.error(
                            f"Bundle type mismatch: expected {bundle_type}, "
                            f"got {metadata.get('type')}"
                        )
                        return False

                return True

        except Exception as e:
            logger.error(f"Bundle validation failed: {e}")
            return False

    @staticmethod
    def import_device_configs(
        bundle_path: Path,
        output_dir: Path,
        overwrite: bool = False,
    ) -> ImportResult:
        """Import device configurations from ZIP bundle.

        Args:
            bundle_path: Path to bundle ZIP file
            output_dir: Directory where configs will be extracted
            overwrite: If True, overwrite existing configs

        Returns:
            ImportResult with import status and details
        """
        result = ImportResult(success=False)

        if not bundle_path.exists():
            result.errors.append(f"Bundle not found: {bundle_path}")
            return result

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(bundle_path, "r") as zf:
                # Read metadata
                metadata_str = zf.read("metadata.json").decode("utf-8")
                metadata = json.loads(metadata_str)

                if metadata.get("type") != "device_configs":
                    result.errors.append(
                        f"Wrong bundle type: {metadata.get('type')}, expected device_configs"
                    )
                    return result

                # Extract configs
                for item in metadata.get("entries", []):
                    config_name = f"configs/{item['name']}.json"
                    if config_name in zf.namelist():
                        try:
                            output_file = output_dir / f"{item['name']}.ini"

                            if output_file.exists() and not overwrite:
                                logger.warning(f"Config already exists (skipping): {output_file}")
                                result.skipped_count += 1
                                continue

                            # Extract and save
                            config_data = json.loads(zf.read(config_name).decode("utf-8"))
                            config_content = ConfigImporter._generate_config_from_data(config_data)

                            with open(output_file, "w") as f:
                                f.write(config_content)

                            result.imported_count += 1

                        except Exception as e:
                            logger.error(f"Failed to import config {item['name']}: {e}")
                            result.errors.append(str(e))

            result.success = result.imported_count > 0
            logger.info(f"Imported {result.imported_count} configs from {bundle_path}")
            return result

        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.errors.append(str(e))
            return result

    @staticmethod
    def _generate_config_from_data(config_data: Dict[str, Any]) -> str:
        """Generate INI config content from extracted data.

        Args:
            config_data: Dictionary with config metadata

        Returns:
            INI-format config file content
        """
        import configparser

        parser = configparser.ConfigParser()

        # Add General section
        parser.add_section("General")
        parser.set("General", "name", config_data.get("name", "unknown"))
        parser.set("General", "device_class", config_data.get("class_name", ""))

        # Add Communications section if available
        comm_type = config_data.get("comm_type", "unknown")
        if comm_type != "unknown":
            parser.add_section("Communications")
            parser.set("Communications", "type", comm_type)

        # Write to string
        import io

        output = io.StringIO()
        parser.write(output)
        return output.getvalue()

    @staticmethod
    def import_templates(
        bundle_path: Path,
        template_manager,
        overwrite: bool = False,
    ) -> ImportResult:
        """Import templates from ZIP bundle.

        Args:
            bundle_path: Path to bundle ZIP file
            template_manager: ConfigTemplateManager instance
            overwrite: If True, overwrite existing templates

        Returns:
            ImportResult with import status and details
        """
        result = ImportResult(success=False)

        if not bundle_path.exists():
            result.errors.append(f"Bundle not found: {bundle_path}")
            return result

        try:
            with zipfile.ZipFile(bundle_path, "r") as zf:
                # Read metadata
                metadata_str = zf.read("metadata.json").decode("utf-8")
                metadata = json.loads(metadata_str)

                if metadata.get("type") != "templates":
                    result.errors.append(
                        f"Wrong bundle type: {metadata.get('type')}, expected templates"
                    )
                    return result

                # Extract templates
                for item in metadata.get("templates", []):
                    template_name = f"templates/{item['name']}.json"
                    if template_name in zf.namelist():
                        try:
                            if item["name"] in template_manager.templates and not overwrite:
                                logger.warning(
                                    f"Template already exists (skipping): {item['name']}"
                                )
                                result.skipped_count += 1
                                continue

                            # Extract and load template
                            template_json = zf.read(template_name).decode("utf-8")
                            template = ConfigTemplate.from_json(template_json)

                            if template_manager.save_template(template):
                                result.imported_count += 1
                            else:
                                result.errors.append(f"Failed to save template: {item['name']}")

                        except Exception as e:
                            logger.error(f"Failed to import template {item['name']}: {e}")
                            result.errors.append(str(e))

            result.success = result.imported_count > 0
            logger.info(f"Imported {result.imported_count} templates from {bundle_path}")
            return result

        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.errors.append(str(e))
            return result
