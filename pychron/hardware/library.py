# ===============================================================================
# Copyright 2024 Jake Ross
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

"""
Hardware device library discovery and metadata parsing.

This module provides infrastructure for discovering registered hardware drivers,
parsing their YAML metadata from class docstrings, validating required fields,
and tracking completeness status for config generation.
"""

import os
import re
import yaml
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class LibraryEntry:
    """
    Represents a hardware device driver with parsed metadata.

    Attributes:
        class_name: Name of the driver class (e.g., 'WatlowEZZone')
        package: Full module path (e.g., 'pychron.hardware.watlow.watlow_ezzone')
        metadata: Dict of parsed YAML metadata from docstring
        is_complete: True if all required fields are present and valid
        missing_fields: List of missing required fields
    """

    class_name: str
    package: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False
    missing_fields: List[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Get device name from metadata or class name fallback."""
        return self.metadata.get("name", self.class_name)

    @property
    def description(self) -> str:
        """Get device description from metadata."""
        return self.metadata.get("description", "")

    @property
    def company(self) -> str:
        """Get company name from metadata."""
        return self.metadata.get("company", "")

    @property
    def docs_url(self) -> Optional[str]:
        """Get documentation URL from metadata."""
        return self.metadata.get("docs_url")

    @property
    def website(self) -> Optional[str]:
        """Get company website from metadata."""
        return self.metadata.get("website")

    @property
    def model(self) -> Optional[str]:
        """Get device model from metadata."""
        return self.metadata.get("model")

    @property
    def vendor_part_number(self) -> Optional[str]:
        """Get vendor part number from metadata."""
        return self.metadata.get("vendor_part_number")

    @property
    def default_comm_type(self) -> str:
        """Get default communication type from metadata or 'ethernet'."""
        return self.metadata.get("default_comm_type", "ethernet")

    @property
    def notes(self) -> Optional[str]:
        """Get additional notes from metadata."""
        return self.metadata.get("notes")

    @property
    def formatted_specs(self) -> Dict[str, str]:
        """Return metadata as formatted specifications table."""
        specs = {
            "Class": self.class_name,
            "Company": self.company or "N/A",
            "Model": self.model or "N/A",
            "Part Number": self.vendor_part_number or "N/A",
            "Comm Type": self.default_comm_type,
            "Status": "Complete" if self.is_complete else "Incomplete",
        }
        return specs

    @property
    def docs_links(self) -> Dict[str, str]:
        """Return all documentation links as a dictionary."""
        links = {}
        if self.docs_url:
            links["Documentation"] = self.docs_url
        if self.website:
            links["Manufacturer"] = self.website
        if self.metadata.get("manual"):
            links["Manual"] = self.metadata["manual"]
        return links

    def has_url(self) -> bool:
        """Check if entry has any URLs (docs or website)."""
        return bool(self.docs_url or self.website)


def parse_docstring_yaml(docstring: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse YAML metadata from a class docstring.

    Expected format:
        '''
        Device description...

        :::
        name: Device Name
        description: Short description
        company: Company Name
        website: https://example.com
        docs_url: https://example.com/docs
        ...
        '''

    Args:
        docstring: The class docstring to parse

    Returns:
        Parsed YAML dict, or None if no metadata block found or parsing failed
    """
    if not docstring:
        return None

    # Find the ::: marker
    lines = docstring.split("\n")
    yaml_start = None
    for i, line in enumerate(lines):
        if line.strip() == ":::":
            yaml_start = i + 1
            break

    if yaml_start is None:
        return None

    # Extract YAML content
    yaml_content = "\n".join(lines[yaml_start:])

    try:
        parsed = yaml.load(yaml_content, Loader=yaml.SafeLoader)
        return parsed if isinstance(parsed, dict) else None
    except yaml.YAMLError:
        return None


def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that required metadata fields are present.

    Required fields: name, description, company, and at least one of docs_url or website

    Args:
        metadata: Dict of metadata fields

    Returns:
        Tuple of (is_valid, missing_fields)
    """
    required_fields = ["name", "description", "company"]
    missing = []

    for field_name in required_fields:
        if field_name not in metadata or not metadata[field_name]:
            missing.append(field_name)

    # Check for at least one link field
    has_link = metadata.get("docs_url") or metadata.get("website")
    if not has_link:
        missing.append("docs_url or website")

    return len(missing) == 0, missing


def load_class(class_name: str, package: str):
    """
    Dynamically import and load a class from a package.

    Args:
        class_name: Name of the class to load
        package: Full module path

    Returns:
        The class, or None if import/attribute lookup fails
    """
    try:
        module = __import__(package, globals(), locals(), [class_name])
        return getattr(module, class_name)
    except (ModuleNotFoundError, AttributeError):
        return None


def discover_library() -> List[LibraryEntry]:
    """
    Discover all registered hardware drivers and parse their metadata.

    Combines drivers from HW_PACKAGE_MAP (core hardware) and PACKAGES (actuators).

    Returns:
        List of LibraryEntry objects with parsed metadata
    """
    from pychron.hardware import HW_PACKAGE_MAP
    from pychron.hardware.actuators import PACKAGES

    entries = []
    all_packages = dict(list(HW_PACKAGE_MAP.items()) + list(PACKAGES.items()))

    for class_name, package in sorted(all_packages.items()):
        klass = load_class(class_name, package)

        # Parse metadata from docstring
        metadata = {}
        if klass and klass.__doc__:
            parsed = parse_docstring_yaml(klass.__doc__)
            if parsed:
                metadata = parsed

        # Validate metadata
        is_complete, missing_fields = validate_metadata(metadata)

        entry = LibraryEntry(
            class_name=class_name,
            package=package,
            metadata=metadata,
            is_complete=is_complete,
            missing_fields=missing_fields,
        )
        entries.append(entry)

    return entries


def get_library_entries() -> List[LibraryEntry]:
    """
    Get all discovered hardware library entries.

    Convenience function that wraps discover_library().

    Returns:
        List of LibraryEntry objects
    """
    return discover_library()


def slugify(name: str) -> str:
    """
    Convert a name to a filesystem-safe slug.

    Converts to lowercase, replaces spaces/special chars with underscores.

    Args:
        name: Name to slugify

    Returns:
        Slugified name suitable for filenames
    """
    slug = re.sub(r"[^\w\s-]", "", name).strip()
    slug = re.sub(r"[-\s]+", "_", slug)
    return slug.lower()


def generate_config_content(
    entry: LibraryEntry, device_name: str, comm_type: str = "ethernet"
) -> str:
    """
    Generate starter device config file content.

    Creates a template config with [General], [Communications], and [Scan] sections.
    Comm type defaults to entry metadata or 'ethernet'.

    Args:
        entry: LibraryEntry with device metadata
        device_name: Display name for the device
        comm_type: Communication type ('ethernet' or 'serial'), defaults to entry.default_comm_type

    Returns:
        Config file content as string
    """
    if comm_type is None:
        comm_type = entry.default_comm_type

    comm_type = comm_type.lower()
    if comm_type not in ("ethernet", "serial"):
        comm_type = "ethernet"

    lines = []

    # General section
    lines.append("[General]")
    lines.append(f"name={device_name}")
    lines.append(f"klass={entry.class_name}")
    if entry.model:
        lines.append(f"model={entry.model}")
    if entry.vendor_part_number:
        lines.append(f"vendor_part_number={entry.vendor_part_number}")
    lines.append("")

    # Communications section
    lines.append("[Communications]")
    lines.append(f"type={comm_type}")

    if comm_type == "ethernet":
        lines.append("host=localhost")
        lines.append("port=10001")
        lines.append("kind=UDP")
    elif comm_type == "serial":
        lines.append("port=/dev/ttyS0")
        lines.append("baudrate=9600")

    lines.append("")

    # Scan section (optional)
    lines.append("[Scan]")
    lines.append("enabled=False")
    lines.append("graph=True")
    lines.append("record=False")
    lines.append("auto_start=False")
    lines.append("period=60")
    lines.append("")

    return "\n".join(lines)


class ConfigGenerationResult:
    """Result of attempting to generate a config file."""

    def __init__(
        self,
        success: bool,
        path: Optional[str] = None,
        error: Optional[str] = None,
        backup_created: bool = False,
    ):
        self.success = success
        self.path = path
        self.error = error
        self.backup_created = backup_created

    def __repr__(self) -> str:
        if self.success:
            msg = f"Config generated: {self.path}"
            if self.backup_created:
                msg += " (backup created)"
            return msg
        else:
            return f"Generation failed: {self.error}"


def generate_device_config(
    entry: LibraryEntry,
    device_name: str,
    output_dir: Optional[Path] = None,
    comm_type: str = "ethernet",
    allow_overwrite: bool = False,
) -> ConfigGenerationResult:
    """
    Generate and write a device config file.

    Creates a starter config in setupfiles/devices/ with filename from device name.
    If file exists and allow_overwrite is False, returns error result.
    If allow_overwrite is True and file exists, backs up existing file first.

    Args:
        entry: LibraryEntry with device metadata
        device_name: Display name for the device
        output_dir: Output directory, defaults to setupfiles/devices
        comm_type: Communication type ('ethernet' or 'serial')
        allow_overwrite: If True, backup and overwrite existing files

    Returns:
        ConfigGenerationResult with success status and details
    """
    if output_dir is None:
        from pychron.paths import paths

        output_dir = Path(paths.device_dir)
    else:
        output_dir = Path(output_dir)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from device name
    filename = f"{slugify(device_name)}.cfg"
    output_path = output_dir / filename

    # Check for collision
    backup_created = False
    if output_path.exists() and not allow_overwrite:
        return ConfigGenerationResult(
            success=False, path=str(output_path), error=f"File already exists: {output_path}"
        )

    # Backup existing file if overwriting
    if output_path.exists() and allow_overwrite:
        backup_path = Path(str(output_path) + ".backup")
        try:
            shutil.copy2(output_path, backup_path)
            backup_created = True
        except (IOError, OSError) as e:
            return ConfigGenerationResult(
                success=False, path=str(output_path), error=f"Failed to backup existing file: {e}"
            )

    # Generate content
    content = generate_config_content(entry, device_name, comm_type)

    # Write file
    try:
        output_path.write_text(content)
        return ConfigGenerationResult(
            success=True, path=str(output_path), backup_created=backup_created
        )
    except (IOError, OSError) as e:
        return ConfigGenerationResult(
            success=False, path=str(output_path), error=f"Failed to write config file: {e}"
        )


# ============= EOF =============================================
