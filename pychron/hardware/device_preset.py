"""Device preset model for lab-specific configurations.

This module provides the DevicePreset class for managing lab-specific
device configuration presets.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
import json


@dataclass
class PresetResult:
    """Result of applying a preset.

    Attributes:
        success: Whether preset application succeeded
        applied_count: Number of configs applied
        skipped_count: Number of configs skipped
        errors: List of error messages
    """

    success: bool
    applied_count: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)

    def __str__(self):
        msg = f"Applied {self.applied_count} configs"
        if self.skipped_count:
            msg += f", skipped {self.skipped_count}"
        if self.errors:
            msg += f"\nErrors: {'; '.join(self.errors[:3])}"
        return msg


@dataclass
class DevicePreset:
    """Model for a device configuration preset.

    A preset is a collection of pre-configured device settings for a specific
    lab environment or use case.

    Attributes:
        name: Preset identifier (e.g., 'nmgrl_production', 'usgs_development')
        lab_name: Lab or environment name (e.g., 'NMGRL', 'USGS', 'Custom')
        device_configs: Dict mapping device class names to config settings
        description: Human-readable description of preset
        version: Preset version string (e.g., '1.0')
        created: Timestamp when preset was created
        modified: Timestamp when preset was last modified
        tags: Optional list of tags for categorization
        auto_activate: Whether to auto-activate when lab is detected
    """

    name: str
    lab_name: str
    device_configs: Dict[str, Dict[str, Any]]
    description: str = ""
    version: str = "1.0"
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    tags: list = field(default_factory=list)
    auto_activate: bool = False

    def apply(self, target_dir: Path) -> PresetResult:
        """Apply preset configurations to target directory.

        Args:
            target_dir: Directory where config files will be written

        Returns:
            PresetResult with application status
        """
        result = PresetResult(success=False)

        try:
            target_dir.mkdir(parents=True, exist_ok=True)

            for device_class, config_data in self.device_configs.items():
                try:
                    config_content = self._generate_config_content(device_class, config_data)

                    # Generate config filename
                    device_name = config_data.get("name", device_class)
                    config_file = target_dir / f"{device_name}.ini"

                    with open(config_file, "w") as f:
                        f.write(config_content)

                    result.applied_count += 1

                except Exception as e:
                    result.errors.append(f"Failed to apply {device_class}: {e}")
                    result.skipped_count += 1

            result.success = result.applied_count > 0
            self.modified = datetime.now()

            return result

        except Exception as e:
            result.errors.append(str(e))
            return result

    def _generate_config_content(self, device_class: str, config_data: Dict[str, Any]) -> str:
        """Generate INI config content from preset data.

        Args:
            device_class: Device class name
            config_data: Configuration settings

        Returns:
            INI-format config file content
        """
        import configparser

        parser = configparser.ConfigParser()

        # Add General section
        parser.add_section("General")
        parser.set("General", "name", config_data.get("name", device_class))
        parser.set("General", "device_class", device_class)

        # Add other sections from config data
        for section, options in config_data.items():
            if section not in ("name", "General"):
                if not parser.has_section(section):
                    parser.add_section(section)
                for key, value in options.items():
                    parser.set(section, key, str(value))

        # Convert to string
        import io

        output = io.StringIO()
        parser.write(output)
        return output.getvalue()

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary for serialization.

        Returns:
            Dictionary representation of preset
        """
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data["created"] = self.created.isoformat()
        data["modified"] = self.modified.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DevicePreset":
        """Create preset from dictionary.

        Args:
            data: Dictionary with preset data

        Returns:
            DevicePreset instance

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
        """Serialize preset to JSON string.

        Returns:
            JSON string representation of preset
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "DevicePreset":
        """Create preset from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            DevicePreset instance

        Raises:
            json.JSONDecodeError: If JSON is invalid
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def add_device_config(self, device_class: str, config: Dict[str, Any]) -> None:
        """Add a device configuration to preset.

        Args:
            device_class: Device class name
            config: Configuration settings
        """
        self.device_configs[device_class] = config
        self.modified = datetime.now()

    def remove_device_config(self, device_class: str) -> bool:
        """Remove a device configuration from preset.

        Args:
            device_class: Device class name

        Returns:
            True if removed, False if not found
        """
        if device_class in self.device_configs:
            del self.device_configs[device_class]
            self.modified = datetime.now()
            return True
        return False

    def get_device_class_list(self) -> List[str]:
        """Get list of device classes in preset.

        Returns:
            Sorted list of device class names
        """
        return sorted(self.device_configs.keys())

    def has_device_class(self, device_class: str) -> bool:
        """Check if preset includes a device class.

        Args:
            device_class: Device class name

        Returns:
            True if preset includes this device class
        """
        return device_class in self.device_configs

    def is_for_lab(self, lab_name: str) -> bool:
        """Check if preset is for a specific lab.

        Args:
            lab_name: Lab name to check

        Returns:
            True if preset is for this lab
        """
        return self.lab_name == lab_name

    def add_tag(self, tag: str) -> None:
        """Add tag to preset.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.modified = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove tag from preset.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.modified = datetime.now()

    def has_tag(self, tag: str) -> bool:
        """Check if preset has a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            True if tag is in preset tags
        """
        return tag in self.tags
