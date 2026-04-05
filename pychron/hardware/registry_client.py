"""Client for syncing with external hardware device registries.

This module provides functionality to fetch, submit, and sync device
metadata with external registry servers.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class RegistryMetadata:
    """Metadata for a device in the registry.

    Attributes:
        class_name: Device class name
        manufacturer: Device manufacturer
        model: Device model
        version: Device version
        last_updated: Last update timestamp
        metadata: Full metadata dictionary
    """

    class_name: str
    manufacturer: str
    model: str
    version: str
    last_updated: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert to dictionary for transmission."""
        return {
            "class_name": self.class_name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SyncResult:
    """Result of a sync operation.

    Attributes:
        success: Whether sync succeeded
        updates_fetched: Number of updates fetched
        updates_submitted: Number of updates submitted
        conflicts: List of conflict messages
        timestamp: When sync occurred
    """

    success: bool
    updates_fetched: int = 0
    updates_submitted: int = 0
    conflicts: List[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def __str__(self):
        msg = f"Sync {'succeeded' if self.success else 'failed'}: "
        msg += f"{self.updates_fetched} updates fetched, "
        msg += f"{self.updates_submitted} updates submitted"
        if self.conflicts:
            msg += f", {len(self.conflicts)} conflicts"
        return msg


class RegistryClient:
    """Client for communicating with hardware device registries.

    Handles fetching device metadata from registries, submitting
    updates, and syncing with external servers.
    """

    def __init__(
        self,
        base_url: str = "https://hardware-registry.example.com/api",
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize registry client.

        Args:
            base_url: Base URL of the registry API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session_id = None
        self._cached_metadata: Dict[str, RegistryMetadata] = {}

    def is_available(self) -> bool:
        """Check if registry is available.

        Returns:
            True if registry is reachable, False otherwise
        """
        try:
            # In production, would make actual HTTP request
            # For now, simulate availability check
            logger.info("Checking registry availability...")
            return True
        except Exception as e:
            logger.error(f"Registry unavailable: {e}")
            return False

    def fetch_device_metadata(self, class_name: str) -> Optional[RegistryMetadata]:
        """Fetch latest metadata for a device from registry.

        Args:
            class_name: Device class name

        Returns:
            RegistryMetadata if found, None otherwise
        """
        try:
            logger.info(f"Fetching metadata for {class_name} from registry...")

            # In production, would make HTTP request to:
            # GET {base_url}/devices/{class_name}

            # Check cache
            if class_name in self._cached_metadata:
                logger.debug(f"Returning cached metadata for {class_name}")
                return self._cached_metadata[class_name]

            # Simulate fetching from registry
            metadata = RegistryMetadata(
                class_name=class_name,
                manufacturer="Unknown",
                model="Unknown",
                version="1.0.0",
                last_updated=datetime.now(),
                metadata={},
            )

            self._cached_metadata[class_name] = metadata
            logger.info(f"Fetched metadata for {class_name}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to fetch metadata for {class_name}: {e}")
            return None

    def submit_device(self, class_name: str, metadata: Dict[str, Any]) -> bool:
        """Submit or update device metadata to registry.

        Args:
            class_name: Device class name
            metadata: Device metadata to submit

        Returns:
            True if submission succeeded, False otherwise
        """
        try:
            logger.info(f"Submitting metadata for {class_name} to registry...")

            # In production, would make HTTP request to:
            # POST {base_url}/devices with metadata

            registry_meta = RegistryMetadata(
                class_name=class_name,
                manufacturer=metadata.get("manufacturer", "Unknown"),
                model=metadata.get("model", "Unknown"),
                version=metadata.get("version", "1.0.0"),
                last_updated=datetime.now(),
                metadata=metadata,
            )

            self._cached_metadata[class_name] = registry_meta
            logger.info(f"Successfully submitted metadata for {class_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to submit device {class_name}: {e}")
            return False

    def check_updates(self) -> List[Tuple[str, str]]:
        """Check for available metadata updates in registry.

        Returns:
            List of (class_name, update_reason) tuples
        """
        try:
            logger.info("Checking for device updates in registry...")

            # In production, would make HTTP request to:
            # GET {base_url}/updates

            # Simulate checking for updates
            updates = []  # No simulated updates

            if updates:
                logger.info(f"Found {len(updates)} available updates")
            else:
                logger.info("No updates available")

            return updates

        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return []

    def get_similar_devices(
        self, class_name: str, manufacturer: str = "", model: str = ""
    ) -> List[Dict]:
        """Find similar devices in registry by name or metadata.

        Args:
            class_name: Device class name to search for
            manufacturer: Optional manufacturer to narrow search
            model: Optional model to narrow search

        Returns:
            List of similar device metadata dicts
        """
        try:
            logger.info(f"Searching registry for devices similar to {class_name}...")

            # In production, would make HTTP request to:
            # GET {base_url}/devices/search?query={class_name}&manufacturer={manufacturer}

            # Simulate search results
            results = []

            logger.info(f"Found {len(results)} similar devices")
            return results

        except Exception as e:
            logger.error(f"Failed to search for similar devices: {e}")
            return []

    def get_device_versions(self, class_name: str) -> List[str]:
        """Get all available versions for a device.

        Args:
            class_name: Device class name

        Returns:
            List of version strings
        """
        try:
            logger.info(f"Fetching available versions for {class_name}...")

            # In production, would make HTTP request to:
            # GET {base_url}/devices/{class_name}/versions

            versions = ["1.0.0"]  # Simulated default version

            return versions

        except Exception as e:
            logger.error(f"Failed to get device versions: {e}")
            return []

    def sync_with_registry(self, local_entries: Dict[str, Any]) -> SyncResult:
        """Perform two-way sync with registry.

        Args:
            local_entries: Dict of local device entries

        Returns:
            SyncResult with sync details
        """
        result = SyncResult(success=True)

        try:
            logger.info("Starting sync with registry...")

            # Fetch updates from registry
            for class_name in local_entries.keys():
                remote_meta = self.fetch_device_metadata(class_name)
                if remote_meta:
                    result.updates_fetched += 1

            # Submit local updates
            for class_name, entry_data in local_entries.items():
                if self.submit_device(class_name, entry_data):
                    result.updates_submitted += 1

            logger.info(f"Sync completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result.success = False
            result.conflicts.append(str(e))
            return result

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics and info.

        Returns:
            Dict with registry statistics
        """
        try:
            logger.info("Fetching registry statistics...")

            # In production, would make HTTP request to:
            # GET {base_url}/stats

            stats = {
                "total_devices": 0,
                "total_versions": 0,
                "manufacturers": 0,
                "last_updated": datetime.now().isoformat(),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get registry stats: {e}")
            return {}

    def export_to_registry_format(self, entry_data: Dict[str, Any]) -> str:
        """Convert local entry to registry format (JSON).

        Args:
            entry_data: Local entry data

        Returns:
            JSON string in registry format
        """
        registry_format = {
            "class_name": entry_data.get("class_name"),
            "manufacturer": entry_data.get("company", entry_data.get("manufacturer")),
            "model": entry_data.get("model"),
            "version": entry_data.get("version", "1.0.0"),
            "description": entry_data.get("description"),
            "comm_type": entry_data.get("default_comm_type"),
            "docs_url": entry_data.get("docs_url"),
            "website": entry_data.get("website"),
            "submitted_at": datetime.now().isoformat(),
        }

        return json.dumps(registry_format, indent=2)

    def clear_cache(self) -> None:
        """Clear cached metadata."""
        self._cached_metadata.clear()
        logger.info("Cleared registry metadata cache")

    def get_cache_size(self) -> int:
        """Get number of cached entries.

        Returns:
            Number of cached metadata entries
        """
        return len(self._cached_metadata)

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with registry (if required).

        Args:
            username: Registry username
            password: Registry password

        Returns:
            True if authentication succeeded, False otherwise
        """
        try:
            logger.info(f"Authenticating with registry as {username}...")

            # In production, would make HTTP request to:
            # POST {base_url}/auth with credentials

            # Simulate authentication
            self.session_id = f"session_{datetime.now().timestamp()}"
            logger.info("Successfully authenticated with registry")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
