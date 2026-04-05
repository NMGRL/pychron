"""Configuration template manager for organizing and persisting templates.

This module provides the ConfigTemplateManager class for loading, saving,
and managing device configuration templates.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import logging

from pychron.hardware.config_template import ConfigTemplate
from pychron.paths import paths

logger = logging.getLogger(__name__)


@dataclass
class TemplateSearchResult:
    """Result of a template search operation.

    Attributes:
        templates: List of matching templates
        total_count: Total number of templates searched
        search_time_ms: Search duration in milliseconds
    """

    templates: List[ConfigTemplate]
    total_count: int
    search_time_ms: float = 0.0


class ConfigTemplateManager:
    """Manager for device configuration templates.

    Handles loading, saving, searching, and managing device configuration
    templates stored in the templates directory.

    Attributes:
        templates_dir: Path to templates directory
        templates: In-memory cache of loaded templates
    """

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        """Initialize template manager.

        Args:
            templates_dir: Override default templates directory path
        """
        if templates_dir is None:
            templates_dir = Path(paths.device_templates_dir)
        elif not isinstance(templates_dir, Path):
            templates_dir = Path(templates_dir)
        self.templates_dir = templates_dir
        self.templates: Dict[str, ConfigTemplate] = {}

    def ensure_templates_dir(self) -> None:
        """Create templates directory if it doesn't exist."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def load_templates(self) -> List[ConfigTemplate]:
        """Load all templates from disk.

        Returns:
            List of loaded ConfigTemplate instances

        Raises:
            IOError: If templates directory cannot be read
        """
        self.ensure_templates_dir()
        self.templates.clear()

        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return []

        templates = []
        for template_file in self.templates_dir.glob("*.json"):
            try:
                template = self._load_template_file(template_file)
                self.templates[template.name] = template
                templates.append(template)
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")

        logger.info(f"Loaded {len(templates)} templates from {self.templates_dir}")
        return sorted(templates, key=lambda t: t.modified, reverse=True)

    def _load_template_file(self, path: Path) -> ConfigTemplate:
        """Load a single template file.

        Args:
            path: Path to template JSON file

        Returns:
            Loaded ConfigTemplate instance

        Raises:
            json.JSONDecodeError: If JSON is invalid
            KeyError: If required fields are missing
        """
        with open(path, "r") as f:
            data = json.load(f)
        return ConfigTemplate.from_dict(data)

    def save_template(self, template: ConfigTemplate) -> bool:
        """Save template to disk.

        Args:
            template: ConfigTemplate to save

        Returns:
            True if save succeeded, False otherwise
        """
        try:
            self.ensure_templates_dir()
            template.modified = datetime.now()

            template_file = self.templates_dir / f"{template.name}.json"
            with open(template_file, "w") as f:
                f.write(template.to_json())

            self.templates[template.name] = template
            logger.info(f"Saved template: {template.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save template {template.name}: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """Delete template from disk and cache.

        Args:
            name: Name of template to delete

        Returns:
            True if delete succeeded, False otherwise
        """
        try:
            template_file = self.templates_dir / f"{name}.json"
            if template_file.exists():
                template_file.unlink()
                self.templates.pop(name, None)
                logger.info(f"Deleted template: {name}")
                return True
            else:
                logger.warning(f"Template file not found: {template_file}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete template {name}: {e}")
            return False

    def get_template(self, name: str) -> Optional[ConfigTemplate]:
        """Get template by name from cache.

        Args:
            name: Template name

        Returns:
            ConfigTemplate if found, None otherwise
        """
        return self.templates.get(name)

    def get_templates_for_device_class(self, device_class: str) -> List[ConfigTemplate]:
        """Get all templates for a specific device class.

        Args:
            device_class: Device class name to filter by

        Returns:
            List of matching templates
        """
        return [t for t in self.templates.values() if t.is_compatible_with(device_class)]

    def get_templates_for_comm_type(self, comm_type: str) -> List[ConfigTemplate]:
        """Get all templates for a specific communication type.

        Args:
            comm_type: Communication type to filter by

        Returns:
            List of matching templates
        """
        return [t for t in self.templates.values() if t.comm_type == comm_type]

    def get_templates_with_tag(self, tag: str) -> List[ConfigTemplate]:
        """Get all templates with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of templates with the tag
        """
        return [t for t in self.templates.values() if t.has_tag(tag)]

    def search_templates(
        self,
        query: str = "",
        device_class: Optional[str] = None,
        comm_type: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> TemplateSearchResult:
        """Search templates with multiple filter criteria.

        Args:
            query: Text to search in name and description
            device_class: Filter by device class
            comm_type: Filter by communication type
            tag: Filter by tag

        Returns:
            TemplateSearchResult with matching templates
        """
        import time

        start = time.time()
        results = list(self.templates.values())

        # Apply text search
        if query:
            query_lower = query.lower()
            results = [
                t
                for t in results
                if query_lower in t.name.lower() or query_lower in t.description.lower()
            ]

        # Apply device class filter
        if device_class:
            results = [t for t in results if t.is_compatible_with(device_class)]

        # Apply comm type filter
        if comm_type:
            results = [t for t in results if t.comm_type == comm_type]

        # Apply tag filter
        if tag:
            results = [t for t in results if t.has_tag(tag)]

        elapsed_ms = (time.time() - start) * 1000
        return TemplateSearchResult(
            templates=sorted(results, key=lambda t: t.modified, reverse=True),
            total_count=len(self.templates),
            search_time_ms=elapsed_ms,
        )

    def rename_template(self, old_name: str, new_name: str) -> bool:
        """Rename an existing template.

        Args:
            old_name: Current template name
            new_name: New template name

        Returns:
            True if rename succeeded, False otherwise
        """
        if old_name not in self.templates:
            logger.warning(f"Template not found: {old_name}")
            return False

        if new_name in self.templates:
            logger.warning(f"Template already exists: {new_name}")
            return False

        try:
            template = self.templates[old_name]
            template.name = new_name
            template.modified = datetime.now()

            # Delete old file and save with new name
            old_file = self.templates_dir / f"{old_name}.json"
            if old_file.exists():
                old_file.unlink()

            self.save_template(template)
            del self.templates[old_name]

            logger.info(f"Renamed template: {old_name} -> {new_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to rename template {old_name}: {e}")
            return False

    def duplicate_template(self, source_name: str, new_name: str) -> Optional[ConfigTemplate]:
        """Create a duplicate of an existing template.

        Args:
            source_name: Name of template to duplicate
            new_name: Name for the duplicate

        Returns:
            New ConfigTemplate instance if successful, None otherwise
        """
        if source_name not in self.templates:
            logger.warning(f"Source template not found: {source_name}")
            return None

        if new_name in self.templates:
            logger.warning(f"Template already exists: {new_name}")
            return None

        try:
            source = self.templates[source_name]
            # Create a new template with copied settings
            duplicate = ConfigTemplate(
                name=new_name,
                device_class=source.device_class,
                comm_type=source.comm_type,
                settings={k: dict(v) for k, v in source.settings.items()},
                description=f"Copy of {source.name}",
                version=source.version,
                tags=list(source.tags),
            )

            if self.save_template(duplicate):
                logger.info(f"Duplicated template: {source_name} -> {new_name}")
                return duplicate
            return None

        except Exception as e:
            logger.error(f"Failed to duplicate template {source_name}: {e}")
            return None

    def export_templates(self, names: List[str], output_path: Path) -> bool:
        """Export multiple templates to a bundle file.

        Args:
            names: List of template names to export
            output_path: Path to write bundle file

        Returns:
            True if export succeeded, False otherwise
        """
        try:
            templates_to_export = []
            for name in names:
                if name in self.templates:
                    templates_to_export.append(self.templates[name])
                else:
                    logger.warning(f"Template not found: {name}")

            if not templates_to_export:
                logger.warning("No templates to export")
                return False

            # Create bundle file
            bundle = {
                "timestamp": datetime.now().isoformat(),
                "count": len(templates_to_export),
                "templates": [t.to_dict() for t in templates_to_export],
            }

            with open(output_path, "w") as f:
                json.dump(bundle, f, indent=2)

            logger.info(f"Exported {len(templates_to_export)} templates to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export templates: {e}")
            return False

    def import_templates(self, bundle_path: Path, overwrite: bool = False) -> int:
        """Import templates from a bundle file.

        Args:
            bundle_path: Path to template bundle file
            overwrite: If True, overwrite existing templates with same name

        Returns:
            Number of templates successfully imported
        """
        try:
            if not bundle_path.exists():
                logger.error(f"Bundle file not found: {bundle_path}")
                return 0

            with open(bundle_path, "r") as f:
                bundle = json.load(f)

            imported_count = 0
            for template_data in bundle.get("templates", []):
                try:
                    template = ConfigTemplate.from_dict(template_data)

                    if template.name in self.templates and not overwrite:
                        logger.warning(f"Template already exists (skipping): {template.name}")
                        continue

                    if self.save_template(template):
                        imported_count += 1

                except Exception as e:
                    logger.error(f"Failed to import template: {e}")

            logger.info(f"Imported {imported_count} templates from {bundle_path}")
            return imported_count

        except Exception as e:
            logger.error(f"Failed to import templates: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about templates.

        Returns:
            Dictionary with template statistics
        """
        device_classes = set()
        comm_types = set()
        all_tags = set()

        for template in self.templates.values():
            device_classes.add(template.device_class)
            comm_types.add(template.comm_type)
            all_tags.update(template.tags)

        return {
            "total_templates": len(self.templates),
            "device_classes": len(device_classes),
            "comm_types": len(comm_types),
            "total_tags": len(all_tags),
            "device_class_list": sorted(device_classes),
            "comm_type_list": sorted(comm_types),
            "tag_list": sorted(all_tags),
        }
