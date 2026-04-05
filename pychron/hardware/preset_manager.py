"""Preset manager for organizing and persisting device presets.

This module provides the PresetManager class for loading, saving, and managing
device configuration presets for different lab environments.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

from pychron.hardware.device_preset import DevicePreset, PresetResult
from pychron.paths import paths

logger = logging.getLogger(__name__)


class PresetManager:
    """Manager for device configuration presets.

    Handles loading, saving, searching, and managing device presets for
    different lab environments and setups.

    Attributes:
        presets_dir: Path to presets directory
        presets: In-memory cache of loaded presets
    """

    def __init__(self, presets_dir: Optional[Path] = None) -> None:
        """Initialize preset manager.

        Args:
            presets_dir: Override default presets directory path
        """
        if presets_dir is None:
            presets_dir = Path(paths.device_presets_dir)
        elif not isinstance(presets_dir, Path):
            presets_dir = Path(presets_dir)
        self.presets_dir = presets_dir
        self.presets: Dict[str, DevicePreset] = {}

    def ensure_presets_dir(self) -> None:
        """Create presets directory if it doesn't exist."""
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def load_presets(self) -> List[DevicePreset]:
        """Load all presets from disk.

        Returns:
            List of loaded DevicePreset instances

        Raises:
            IOError: If presets directory cannot be read
        """
        self.ensure_presets_dir()
        self.presets.clear()

        if not self.presets_dir.exists():
            logger.warning(f"Presets directory not found: {self.presets_dir}")
            return []

        presets = []
        for preset_file in self.presets_dir.glob("*.json"):
            try:
                preset = self._load_preset_file(preset_file)
                self.presets[preset.name] = preset
                presets.append(preset)
            except Exception as e:
                logger.error(f"Failed to load preset {preset_file}: {e}")

        logger.info(f"Loaded {len(presets)} presets from {self.presets_dir}")
        return sorted(presets, key=lambda p: p.modified, reverse=True)

    def _load_preset_file(self, path: Path) -> DevicePreset:
        """Load a single preset file.

        Args:
            path: Path to preset JSON file

        Returns:
            Loaded DevicePreset instance

        Raises:
            json.JSONDecodeError: If JSON is invalid
            KeyError: If required fields are missing
        """
        with open(path, "r") as f:
            data = json.load(f)
        return DevicePreset.from_dict(data)

    def save_preset(self, preset: DevicePreset) -> bool:
        """Save preset to disk.

        Args:
            preset: DevicePreset to save

        Returns:
            True if save succeeded, False otherwise
        """
        try:
            self.ensure_presets_dir()
            preset.modified = datetime.now()

            preset_file = self.presets_dir / f"{preset.name}.json"
            with open(preset_file, "w") as f:
                f.write(preset.to_json())

            self.presets[preset.name] = preset
            logger.info(f"Saved preset: {preset.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save preset {preset.name}: {e}")
            return False

    def delete_preset(self, name: str) -> bool:
        """Delete preset from disk and cache.

        Args:
            name: Name of preset to delete

        Returns:
            True if delete succeeded, False otherwise
        """
        try:
            preset_file = self.presets_dir / f"{name}.json"
            if preset_file.exists():
                preset_file.unlink()
                self.presets.pop(name, None)
                logger.info(f"Deleted preset: {name}")
                return True
            else:
                logger.warning(f"Preset file not found: {preset_file}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete preset {name}: {e}")
            return False

    def get_preset(self, name: str) -> Optional[DevicePreset]:
        """Get preset by name from cache.

        Args:
            name: Preset name

        Returns:
            DevicePreset if found, None otherwise
        """
        return self.presets.get(name)

    def get_presets_for_lab(self, lab_name: str) -> List[DevicePreset]:
        """Get all presets for a specific lab.

        Args:
            lab_name: Lab name to filter by

        Returns:
            List of presets for the lab
        """
        return [p for p in self.presets.values() if p.is_for_lab(lab_name)]

    def get_presets_with_device_class(self, device_class: str) -> List[DevicePreset]:
        """Get all presets that include a specific device class.

        Args:
            device_class: Device class name

        Returns:
            List of matching presets
        """
        return [p for p in self.presets.values() if p.has_device_class(device_class)]

    def get_presets_with_tag(self, tag: str) -> List[DevicePreset]:
        """Get all presets with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of presets with the tag
        """
        return [p for p in self.presets.values() if p.has_tag(tag)]

    def get_auto_activate_presets(self) -> List[DevicePreset]:
        """Get presets that should auto-activate.

        Returns:
            List of presets with auto_activate=True
        """
        return [p for p in self.presets.values() if p.auto_activate]

    def search_presets(
        self,
        query: str = "",
        lab_name: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[DevicePreset]:
        """Search presets with multiple filter criteria.

        Args:
            query: Text to search in name and description
            lab_name: Filter by lab name
            tag: Filter by tag

        Returns:
            List of matching presets
        """
        results = list(self.presets.values())

        # Apply text search
        if query:
            query_lower = query.lower()
            results = [
                p
                for p in results
                if query_lower in p.name.lower() or query_lower in p.description.lower()
            ]

        # Apply lab filter
        if lab_name:
            results = [p for p in results if p.is_for_lab(lab_name)]

        # Apply tag filter
        if tag:
            results = [p for p in results if p.has_tag(tag)]

        return sorted(results, key=lambda p: p.modified, reverse=True)

    def apply_preset(self, name: str, target_dir: Path) -> PresetResult:
        """Apply a preset to target directory.

        Args:
            name: Name of preset to apply
            target_dir: Target directory for config files

        Returns:
            PresetResult with application status
        """
        preset = self.get_preset(name)
        if not preset:
            return PresetResult(success=False, errors=[f"Preset not found: {name}"])

        return preset.apply(target_dir)

    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """Rename an existing preset.

        Args:
            old_name: Current preset name
            new_name: New preset name

        Returns:
            True if rename succeeded, False otherwise
        """
        if old_name not in self.presets:
            logger.warning(f"Preset not found: {old_name}")
            return False

        if new_name in self.presets:
            logger.warning(f"Preset already exists: {new_name}")
            return False

        try:
            preset = self.presets[old_name]
            preset.name = new_name
            preset.modified = datetime.now()

            # Delete old file and save with new name
            old_file = self.presets_dir / f"{old_name}.json"
            if old_file.exists():
                old_file.unlink()

            self.save_preset(preset)
            del self.presets[old_name]

            logger.info(f"Renamed preset: {old_name} -> {new_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to rename preset {old_name}: {e}")
            return False

    def duplicate_preset(self, source_name: str, new_name: str) -> Optional[DevicePreset]:
        """Create a duplicate of an existing preset.

        Args:
            source_name: Name of preset to duplicate
            new_name: Name for the duplicate

        Returns:
            New DevicePreset instance if successful, None otherwise
        """
        if source_name not in self.presets:
            logger.warning(f"Source preset not found: {source_name}")
            return None

        if new_name in self.presets:
            logger.warning(f"Preset already exists: {new_name}")
            return None

        try:
            source = self.presets[source_name]
            # Create a new preset with copied configs
            duplicate = DevicePreset(
                name=new_name,
                lab_name=source.lab_name,
                device_configs={k: dict(v) for k, v in source.device_configs.items()},
                description=f"Copy of {source.name}",
                version=source.version,
                tags=list(source.tags),
            )

            if self.save_preset(duplicate):
                logger.info(f"Duplicated preset: {source_name} -> {new_name}")
                return duplicate
            return None

        except Exception as e:
            logger.error(f"Failed to duplicate preset {source_name}: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about presets.

        Returns:
            Dictionary with preset statistics
        """
        labs = set()
        all_device_classes = set()
        all_tags = set()

        for preset in self.presets.values():
            labs.add(preset.lab_name)
            all_device_classes.update(preset.device_configs.keys())
            all_tags.update(preset.tags)

        return {
            "total_presets": len(self.presets),
            "labs": len(labs),
            "device_classes": len(all_device_classes),
            "total_tags": len(all_tags),
            "lab_list": sorted(labs),
            "device_class_list": sorted(all_device_classes),
            "tag_list": sorted(all_tags),
        }

    def create_builtin_presets(self) -> None:
        """Create built-in presets for common labs.

        This method creates default presets for NMGRL and USGS labs if they
        don't already exist.
        """
        # NMGRL preset
        if "nmgrl_default" not in self.presets:
            nmgrl = DevicePreset(
                name="nmgrl_default",
                lab_name="NMGRL",
                device_configs={},
                description="Default NMGRL lab configuration",
                tags=["production", "nmgrl"],
                auto_activate=False,
            )
            self.save_preset(nmgrl)

        # USGS preset
        if "usgs_default" not in self.presets:
            usgs = DevicePreset(
                name="usgs_default",
                lab_name="USGS",
                device_configs={},
                description="Default USGS lab configuration",
                tags=["production", "usgs"],
                auto_activate=False,
            )
            self.save_preset(usgs)

        logger.info("Created built-in presets")
