"""Device lifecycle tracking for version management and updates.

This module provides functionality to track device versions, availability
of updates, deprecation status, and compatibility matrices.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VersionStatus(Enum):
    """Device version status enumeration."""

    CURRENT = "current"
    LEGACY = "legacy"
    DEPRECATED = "deprecated"
    BETA = "beta"


@dataclass
class DeviceVersion:
    """Represents a specific version of a device driver.

    Attributes:
        version: Semantic version string (e.g., '1.0.0')
        release_date: Date the version was released
        status: Version status (current, legacy, deprecated, beta)
        changelog: Description of changes in this version
        compatible_with: List of other device versions this is compatible with
        download_url: URL where this version can be downloaded
        release_notes: Detailed release notes
    """

    version: str
    release_date: datetime
    status: VersionStatus
    changelog: str
    compatible_with: List[str] = field(default_factory=list)
    download_url: str = ""
    release_notes: str = ""

    def is_current(self) -> bool:
        """Check if this version is the current/stable version."""
        return self.status == VersionStatus.CURRENT

    def is_deprecated(self) -> bool:
        """Check if this version is deprecated."""
        return self.status == VersionStatus.DEPRECATED

    def is_compatible_with(self, other_version: str) -> bool:
        """Check compatibility with another version.

        Args:
            other_version: Version string to check compatibility with

        Returns:
            True if compatible, False otherwise
        """
        return other_version in self.compatible_with

    def days_since_release(self) -> int:
        """Get number of days since release.

        Returns:
            Days since this version was released
        """
        return (datetime.now() - self.release_date).days

    def is_recent(self, days: int = 30) -> bool:
        """Check if version is recent.

        Args:
            days: Number of days to consider as "recent"

        Returns:
            True if released within specified days
        """
        return self.days_since_release() <= days


@dataclass
class DeviceLifecycle:
    """Manages the lifecycle of a device driver.

    Attributes:
        device_class: Name of the device class
        versions: List of all device versions
        current_version: Current recommended version
        installed_version: Currently installed version (if any)
        created_at: When device was first tracked
        deprecated_at: When device was deprecated (if applicable)
    """

    device_class: str
    versions: List[DeviceVersion] = field(default_factory=list)
    current_version: str = ""
    installed_version: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    deprecated_at: Optional[datetime] = None

    @property
    def needs_update(self) -> bool:
        """Check if installed version is outdated.

        Returns:
            True if update is available and installed version differs from current
        """
        if not self.installed_version or not self.current_version:
            return False
        return self.installed_version != self.current_version

    @property
    def is_deprecated(self) -> bool:
        """Check if device is deprecated.

        Returns:
            True if deprecation date is set
        """
        return self.deprecated_at is not None

    @property
    def latest_version(self) -> Optional[DeviceVersion]:
        """Get the latest version of the device.

        Returns:
            DeviceVersion with latest version, or None if no versions
        """
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.release_date)

    @property
    def current_version_obj(self) -> Optional[DeviceVersion]:
        """Get the current version object.

        Returns:
            Current DeviceVersion, or None if not found
        """
        if not self.current_version:
            return None
        for v in self.versions:
            if v.version == self.current_version:
                return v
        return None

    @property
    def installed_version_obj(self) -> Optional[DeviceVersion]:
        """Get the installed version object.

        Returns:
            Installed DeviceVersion, or None if not found
        """
        if not self.installed_version:
            return None
        for v in self.versions:
            if v.version == self.installed_version:
                return v
        return None

    def add_version(self, version: DeviceVersion) -> None:
        """Add a new version to the lifecycle.

        Args:
            version: DeviceVersion to add
        """
        # Remove existing version with same version string
        self.versions = [v for v in self.versions if v.version != version.version]
        self.versions.append(version)
        logger.info(f"Added version {version.version} for {self.device_class}")

    def get_compatible_versions(self, version: str) -> List[DeviceVersion]:
        """Get all versions compatible with a specific version.

        Args:
            version: Version string to find compatible versions for

        Returns:
            List of compatible DeviceVersion objects
        """
        compatible = []
        for v in self.versions:
            if v.is_compatible_with(version):
                compatible.append(v)
        return compatible

    def get_versions_since(self, date: datetime) -> List[DeviceVersion]:
        """Get all versions released after a specific date.

        Args:
            date: Release date threshold

        Returns:
            List of DeviceVersion objects released after date
        """
        return [v for v in self.versions if v.release_date > date]

    def mark_deprecated(self) -> None:
        """Mark this device as deprecated."""
        self.deprecated_at = datetime.now()
        logger.info(f"Marked {self.device_class} as deprecated")

    def unmark_deprecated(self) -> None:
        """Unmark deprecation status."""
        self.deprecated_at = None
        logger.info(f"Unmarked {self.device_class} as deprecated")

    def mark_installed(self, version: str) -> bool:
        """Mark a version as installed.

        Args:
            version: Version string to mark as installed

        Returns:
            True if version found and marked, False otherwise
        """
        # Check version exists
        if not any(v.version == version for v in self.versions):
            logger.warning(f"Version {version} not found for {self.device_class}")
            return False

        self.installed_version = version
        logger.info(f"Marked version {version} as installed for {self.device_class}")
        return True

    def get_update_path(self) -> Optional[List[str]]:
        """Get recommended update path from installed to current version.

        Returns:
            List of version strings to follow for updates, or None if not needed
        """
        if not self.needs_update or not self.installed_version:
            return None

        # For simplicity, return direct path
        # In production, could find optimal upgrade path through compatibility
        return [self.installed_version, self.current_version]


class LifecycleManager:
    """Manager for device lifecycle tracking and updates.

    Handles tracking device versions, checking for updates,
    and managing deprecation status.
    """

    def __init__(self) -> None:
        """Initialize lifecycle manager."""
        self.lifecycles: Dict[str, DeviceLifecycle] = {}

    def register_device(self, device_class: str) -> DeviceLifecycle:
        """Register a device for lifecycle tracking.

        Args:
            device_class: Device class name to register

        Returns:
            DeviceLifecycle for the registered device
        """
        if device_class not in self.lifecycles:
            lifecycle = DeviceLifecycle(device_class=device_class)
            self.lifecycles[device_class] = lifecycle
            logger.info(f"Registered device for lifecycle tracking: {device_class}")
        return self.lifecycles[device_class]

    def get_lifecycle(self, device_class: str) -> Optional[DeviceLifecycle]:
        """Get lifecycle for a device.

        Args:
            device_class: Device class name

        Returns:
            DeviceLifecycle if registered, None otherwise
        """
        return self.lifecycles.get(device_class)

    def add_version(self, device_class: str, version: DeviceVersion) -> bool:
        """Add a version to a device.

        Args:
            device_class: Device class name
            version: DeviceVersion to add

        Returns:
            True if successful, False if device not registered
        """
        lifecycle = self.get_lifecycle(device_class)
        if not lifecycle:
            logger.warning(f"Device not registered: {device_class}")
            return False

        lifecycle.add_version(version)
        return True

    def check_for_updates(self) -> List[Tuple[str, str, str]]:
        """Check for available updates across all devices.

        Returns:
            List of (device_class, installed_version, current_version) tuples
        """
        updates_available = []

        for device_class, lifecycle in self.lifecycles.items():
            if lifecycle.needs_update:
                updates_available.append(
                    (device_class, lifecycle.installed_version, lifecycle.current_version)
                )

        logger.info(f"Found {len(updates_available)} devices with available updates")
        return updates_available

    def get_deprecated_devices(self) -> List[str]:
        """Get list of deprecated devices.

        Returns:
            List of deprecated device class names
        """
        deprecated = [
            device_class
            for device_class, lifecycle in self.lifecycles.items()
            if lifecycle.is_deprecated
        ]
        return deprecated

    def get_compatibility_warnings(self) -> List[str]:
        """Get compatibility warnings for installed versions.

        Returns:
            List of compatibility warning messages
        """
        warnings = []

        for device_class, lifecycle in self.lifecycles.items():
            if not lifecycle.installed_version or not lifecycle.current_version_obj:
                continue

            current = lifecycle.current_version_obj
            installed = lifecycle.installed_version_obj

            if installed and not installed.is_compatible_with(current.version):
                warnings.append(
                    f"{device_class}: Installed version {installed.version} "
                    f"may not be compatible with current version {current.version}"
                )

        return warnings

    def get_update_statistics(self) -> Dict[str, int]:
        """Get statistics about device updates.

        Returns:
            Dict with update statistics
        """
        updates_needed = sum(1 for l in self.lifecycles.values() if l.needs_update)
        deprecated_count = len(self.get_deprecated_devices())
        total_devices = len(self.lifecycles)

        return {
            "total_devices": total_devices,
            "updates_needed": updates_needed,
            "deprecated_devices": deprecated_count,
            "up_to_date": total_devices - updates_needed,
        }

    def get_version_timeline(self, device_class: str) -> List[Tuple[str, datetime]]:
        """Get version release timeline for a device.

        Args:
            device_class: Device class name

        Returns:
            List of (version, release_date) tuples sorted chronologically
        """
        lifecycle = self.get_lifecycle(device_class)
        if not lifecycle:
            return []

        timeline = [(v.version, v.release_date) for v in lifecycle.versions]
        return sorted(timeline, key=lambda x: x[1])

    def get_support_status(self, device_class: str, version: str) -> Optional[str]:
        """Get support status for a specific device version.

        Args:
            device_class: Device class name
            version: Version string

        Returns:
            Support status string or None if version not found
        """
        lifecycle = self.get_lifecycle(device_class)
        if not lifecycle:
            return None

        for v in lifecycle.versions:
            if v.version == version:
                if v.status == VersionStatus.CURRENT:
                    return "Supported (Current)"
                elif v.status == VersionStatus.LEGACY:
                    return "Limited Support (Legacy)"
                elif v.status == VersionStatus.DEPRECATED:
                    return "Unsupported (Deprecated)"
                elif v.status == VersionStatus.BETA:
                    return "Testing (Beta)"

        return None
