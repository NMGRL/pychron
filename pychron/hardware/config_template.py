"""Configuration template model for hardware device configs.

This module provides the ConfigTemplate class for managing device configuration
templates. Templates allow saving and reusing device configurations across
multiple setups (lab-specific, experiment-specific, etc.).
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import configparser
import json


@dataclass
class ConfigTemplate:
    """Model for a device configuration template.

    Attributes:
        name: Template identifier (e.g., 'nmgrl_default', 'usgs_setup')
        device_class: Target device class name (e.g., 'PychronDiodeVoltageSupply')
        comm_type: Communication type (e.g., 'RS232', 'GPIB', 'USB')
        settings: Dict of config sections and their key-value pairs
        description: Human-readable description of template purpose
        created: Timestamp when template was created
        modified: Timestamp when template was last modified
        version: Template version string (e.g., '1.0')
        tags: Optional list of tags for categorization
    """

    name: str
    device_class: str
    comm_type: str
    settings: Dict[str, Dict[str, Any]]
    description: str = ""
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    tags: list = field(default_factory=list)

    def to_config_content(self, device_name: str) -> str:
        """Generate config file content from template.

        Args:
            device_name: Name of the device to use in config

        Returns:
            String content suitable for writing to .INI config file
        """
        config = configparser.ConfigParser()

        # Add device name and class info
        if "General" not in self.settings:
            config.add_section("General")
        config.set("General", "name", device_name)
        config.set("General", "device_class", self.device_class)

        # Add all template settings sections
        for section, options in self.settings.items():
            if section == "General" and config.has_section("General"):
                # Merge with existing General section
                for key, value in options.items():
                    if key != "name":  # Keep the device_name set above
                        config.set("General", key, str(value))
            else:
                if not config.has_section(section):
                    config.add_section(section)
                for key, value in options.items():
                    config.set(section, key, str(value))

        # Convert to string
        import io

        output = io.StringIO()
        config.write(output)
        return output.getvalue()

    @classmethod
    def from_config_file(cls, path: Path, name: str) -> "ConfigTemplate":
        """Load template from existing config file.

        Args:
            path: Path to .INI config file
            name: Name to assign to template

        Returns:
            ConfigTemplate instance loaded from config file

        Raises:
            FileNotFoundError: If config file doesn't exist
            configparser.Error: If config file is malformed
        """
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        config = configparser.ConfigParser()
        config.read(path)

        # Extract device class if available in General section
        device_class = "UnknownDevice"
        if config.has_section("General"):
            device_class = config.get("General", "device_class", fallback="UnknownDevice")

        # Extract all settings
        settings = {}
        for section in config.sections():
            settings[section] = dict(config.items(section))

        # Infer comm_type from Communications section if available
        comm_type = "Unknown"
        if "Communications" in settings:
            comm_type = settings["Communications"].get("comm_type", "Unknown")

        return cls(
            name=name,
            device_class=device_class,
            comm_type=comm_type,
            settings=settings,
            description=f"Template loaded from {path.name}",
            created=datetime.fromtimestamp(path.stat().st_ctime),
            modified=datetime.fromtimestamp(path.stat().st_mtime),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization.

        Returns:
            Dictionary representation of template
        """
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data["created"] = self.created.isoformat()
        data["modified"] = self.modified.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigTemplate":
        """Create template from dictionary.

        Args:
            data: Dictionary with template data

        Returns:
            ConfigTemplate instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If datetime strings are invalid
        """
        # Parse datetime strings
        if isinstance(data.get("created"), str):
            data["created"] = datetime.fromisoformat(data["created"])
        if isinstance(data.get("modified"), str):
            data["modified"] = datetime.fromisoformat(data["modified"])

        return cls(**data)

    def to_json(self) -> str:
        """Serialize template to JSON string.

        Returns:
            JSON string representation of template
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ConfigTemplate":
        """Create template from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            ConfigTemplate instance

        Raises:
            json.JSONDecodeError: If JSON is invalid
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def is_compatible_with(self, device_class: str) -> bool:
        """Check if template is compatible with device class.

        Args:
            device_class: Device class to check compatibility with

        Returns:
            True if template is for this device class
        """
        return self.device_class == device_class

    def has_tag(self, tag: str) -> bool:
        """Check if template has a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            True if tag is in template tags
        """
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        """Add tag to template.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.modified = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove tag from template.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.modified = datetime.now()
