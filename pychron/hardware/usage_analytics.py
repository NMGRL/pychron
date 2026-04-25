"""Device usage analytics and statistics tracking.

This module provides functionality to track device usage statistics,
success rates, error frequencies, and generate analytics reports.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class DeviceUsageEvent:
    """Single device usage event.

    Attributes:
        device_class: Device class name
        timestamp: When the event occurred
        duration: How long the operation took
        success: Whether operation was successful
        error_type: Type of error if failed (None if successful)
        metadata: Additional metadata about the event
    """

    device_class: str
    timestamp: datetime
    duration: timedelta
    success: bool
    error_type: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "device_class": self.device_class,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration.total_seconds(),
            "success": self.success,
            "error_type": self.error_type,
            "metadata": self.metadata,
        }


@dataclass
class DeviceUsageStats:
    """Statistics for a device's usage.

    Attributes:
        device_class: Device class name
        total_runs: Total number of operations
        successful_runs: Number of successful operations
        total_runtime: Total runtime across all operations
        last_used: Last time device was used
        error_count: Number of failed operations
        error_types: Dict of error type -> count
        average_runtime: Average runtime per operation
    """

    device_class: str
    total_runs: int = 0
    successful_runs: int = 0
    total_runtime: timedelta = field(default_factory=lambda: timedelta(0))
    last_used: Optional[datetime] = None
    error_count: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100

    @property
    def failure_rate(self) -> float:
        """Get failure rate percentage."""
        return 100.0 - self.success_rate

    @property
    def average_runtime(self) -> timedelta:
        """Get average runtime per operation."""
        if self.total_runs == 0:
            return timedelta(0)
        return self.total_runtime / self.total_runs

    @property
    def reliability_score(self) -> float:
        """Get reliability score (0-100)."""
        return self.success_rate

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "device_class": self.device_class,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "total_runtime_hours": self.total_runtime.total_seconds() / 3600,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "average_runtime_seconds": self.average_runtime.total_seconds(),
            "reliability_score": self.reliability_score,
            "error_types": self.error_types,
        }


class UsageAnalytics:
    """Analytics engine for device usage tracking.

    Tracks device usage events and generates analytics reports
    on usage patterns, reliability, and performance.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        """Initialize analytics engine.

        Args:
            data_dir: Directory for persisting analytics data
        """
        self.data_dir = data_dir or Path.home() / ".pychron" / "analytics"
        self.device_stats: Dict[str, DeviceUsageStats] = {}
        self.events: List[DeviceUsageEvent] = []
        self._load_stats()

    def _load_stats(self) -> None:
        """Load saved statistics from disk."""
        if not self.data_dir.exists():
            return

        stats_file = self.data_dir / "device_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, "r") as f:
                    data = json.load(f)
                    for device_class, stats_data in data.items():
                        stats = DeviceUsageStats(device_class=device_class)
                        stats.total_runs = stats_data.get("total_runs", 0)
                        stats.successful_runs = stats_data.get("successful_runs", 0)
                        stats.total_runtime = timedelta(
                            seconds=stats_data.get("total_runtime_seconds", 0)
                        )
                        if stats_data.get("last_used"):
                            stats.last_used = datetime.fromisoformat(stats_data["last_used"])
                        stats.error_count = stats_data.get("error_count", 0)
                        stats.error_types = stats_data.get("error_types", {})
                        self.device_stats[device_class] = stats

                logger.info(f"Loaded analytics for {len(self.device_stats)} devices")
            except Exception as e:
                logger.warning(f"Failed to load analytics: {e}")

    def _save_stats(self) -> None:
        """Save statistics to disk."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            stats_file = self.data_dir / "device_stats.json"

            data = {}
            for device_class, stats in self.device_stats.items():
                data[device_class] = {
                    "total_runs": stats.total_runs,
                    "successful_runs": stats.successful_runs,
                    "total_runtime_seconds": stats.total_runtime.total_seconds(),
                    "last_used": stats.last_used.isoformat() if stats.last_used else None,
                    "error_count": stats.error_count,
                    "error_types": stats.error_types,
                }

            with open(stats_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save analytics: {e}")

    def record_event(self, event: DeviceUsageEvent) -> None:
        """Record a device usage event.

        Args:
            event: DeviceUsageEvent to record
        """
        # Initialize stats if needed
        if event.device_class not in self.device_stats:
            self.device_stats[event.device_class] = DeviceUsageStats(
                device_class=event.device_class
            )

        stats = self.device_stats[event.device_class]

        # Update statistics
        stats.total_runs += 1
        stats.total_runtime += event.duration
        stats.last_used = event.timestamp

        if event.success:
            stats.successful_runs += 1
        else:
            stats.error_count += 1
            if event.error_type:
                stats.error_types[event.error_type] = stats.error_types.get(event.error_type, 0) + 1

        self.events.append(event)
        self._save_stats()

        logger.debug(
            f"Recorded event for {event.device_class}: "
            f"{'success' if event.success else 'failure'}"
        )

    def get_device_stats(self, device_class: str) -> Optional[DeviceUsageStats]:
        """Get statistics for a device.

        Args:
            device_class: Device class name

        Returns:
            DeviceUsageStats or None if device has no recorded events
        """
        return self.device_stats.get(device_class)

    def get_top_devices(self, limit: int = 10, by: str = "runs") -> List[DeviceUsageStats]:
        """Get top devices by specified metric.

        Args:
            limit: Maximum number of devices to return
            by: Metric to sort by ('runs', 'success_rate', 'reliability')

        Returns:
            List of top DeviceUsageStats
        """
        if by == "runs":
            sorted_stats = sorted(
                self.device_stats.values(), key=lambda s: s.total_runs, reverse=True
            )
        elif by == "success_rate":
            sorted_stats = sorted(
                self.device_stats.values(), key=lambda s: s.success_rate, reverse=True
            )
        elif by == "reliability":
            sorted_stats = sorted(
                self.device_stats.values(),
                key=lambda s: s.reliability_score,
                reverse=True,
            )
        else:
            return []

        return sorted_stats[:limit]

    def get_reliability_report(self) -> Dict[str, float]:
        """Get reliability (success rate) for all devices.

        Returns:
            Dict mapping device class to success rate percentage
        """
        return {
            device_class: stats.success_rate for device_class, stats in self.device_stats.items()
        }

    def get_least_reliable_devices(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get least reliable devices.

        Args:
            limit: Maximum number of devices to return

        Returns:
            List of (device_class, failure_rate) tuples
        """
        devices = [
            (device_class, stats.failure_rate) for device_class, stats in self.device_stats.items()
        ]
        devices.sort(key=lambda x: x[1], reverse=True)
        return devices[:limit]

    def get_errors_by_device(self) -> Dict[str, Dict[str, int]]:
        """Get error types grouped by device.

        Returns:
            Dict mapping device class to error type counts
        """
        return {
            device_class: dict(stats.error_types)
            for device_class, stats in self.device_stats.items()
        }

    def get_total_runtime(self) -> timedelta:
        """Get total runtime across all devices.

        Returns:
            Total timedelta
        """
        return sum(
            (stats.total_runtime for stats in self.device_stats.values()),
            timedelta(0),
        )

    def get_summary_statistics(self) -> Dict:
        """Get overall summary statistics.

        Returns:
            Dict with summary stats
        """
        total_runs = sum(s.total_runs for s in self.device_stats.values())
        successful_runs = sum(s.successful_runs for s in self.device_stats.values())
        total_errors = sum(s.error_count for s in self.device_stats.values())

        return {
            "total_devices": len(self.device_stats),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "total_errors": total_errors,
            "overall_success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0.0,
            "total_runtime_hours": self.get_total_runtime().total_seconds() / 3600,
            "average_runtime_per_run_seconds": (
                self.get_total_runtime().total_seconds() / total_runs if total_runs > 0 else 0
            ),
        }

    def get_events_for_device(
        self, device_class: str, since: Optional[datetime] = None
    ) -> List[DeviceUsageEvent]:
        """Get usage events for a device.

        Args:
            device_class: Device class name
            since: Optional date to filter events after

        Returns:
            List of DeviceUsageEvent
        """
        events = [e for e in self.events if e.device_class == device_class]

        if since:
            events = [e for e in events if e.timestamp >= since]

        return sorted(events, key=lambda e: e.timestamp, reverse=True)

    def get_events_since(self, date: datetime) -> List[DeviceUsageEvent]:
        """Get all events since a specific date.

        Args:
            date: Date threshold

        Returns:
            List of DeviceUsageEvent after date
        """
        return sorted([e for e in self.events if e.timestamp >= date], key=lambda e: e.timestamp)

    def reset_device_stats(self, device_class: str) -> bool:
        """Reset statistics for a device.

        Args:
            device_class: Device class name to reset

        Returns:
            True if device was reset, False if not found
        """
        if device_class in self.device_stats:
            del self.device_stats[device_class]
            self.events = [e for e in self.events if e.device_class != device_class]
            self._save_stats()
            logger.info(f"Reset statistics for {device_class}")
            return True
        return False

    def clear_old_events(self, days: int = 90) -> int:
        """Remove events older than specified number of days.

        Args:
            days: Number of days to keep

        Returns:
            Number of events removed
        """
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self.events)
        self.events = [e for e in self.events if e.timestamp >= cutoff]
        removed = original_count - len(self.events)

        if removed > 0:
            logger.info(f"Removed {removed} events older than {days} days")

        return removed

    def export_statistics(self, output_path: Path, format: str = "json") -> bool:
        """Export analytics to file.

        Args:
            output_path: Path where analytics will be written
            format: Export format ('json' or 'csv')

        Returns:
            True if export succeeded, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format == "json":
                data = {
                    device_class: stats.to_dict()
                    for device_class, stats in self.device_stats.items()
                }
                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2)

            elif format == "csv":
                import csv

                with open(output_path, "w", newline="") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "device_class",
                            "total_runs",
                            "successful_runs",
                            "success_rate",
                            "reliability_score",
                        ],
                    )
                    writer.writeheader()
                    for stats in self.device_stats.values():
                        writer.writerow(
                            {
                                "device_class": stats.device_class,
                                "total_runs": stats.total_runs,
                                "successful_runs": stats.successful_runs,
                                "success_rate": f"{stats.success_rate:.1f}%",
                                "reliability_score": f"{stats.reliability_score:.1f}",
                            }
                        )

            logger.info(f"Exported analytics to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            return False
