"""Data classes for Prometheus observability events."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PrometheusEvent:
    """Represents a single metrics event (counter, gauge, histogram operation).

    Attributes:
        timestamp: Unix timestamp when event occurred
        event_type: Type of event ("counter", "gauge", "histogram")
        metric_name: Full metric name (e.g., "pychron_runs_started_total")
        value: Numeric value or delta for the metric
        labels: Dict of label names to values (e.g., {"device": "furnace"})
        status: "success" or error message
    """

    timestamp: float
    event_type: str  # "counter", "gauge", "histogram"
    metric_name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    status: str = "success"

    def to_dict(self) -> Dict:
        """Convert event to dictionary for export."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "metric_name": self.metric_name,
            "value": self.value,
            "labels": self.labels,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PrometheusEvent":
        """Create event from dictionary."""
        return cls(**data)
