"""JSONL-based telemetry recorder with buffering."""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
import os

from .event import TelemetryEvent
from .context import TelemetryContext


class TelemetryRecorder:
    """Thread-safe JSONL telemetry recorder with buffering.

    Buffers events in memory and writes them in batches to reduce I/O overhead.
    Automatically creates log directory if it doesn't exist.
    """

    def __init__(
        self,
        log_path: Path,
        max_buffer_size: int = 100,
        auto_flush_interval: Optional[float] = None,
    ):
        """Initialize recorder.

        Args:
            log_path: Path to JSONL file to write
            max_buffer_size: Number of events to buffer before flushing
            auto_flush_interval: If set, flush periodically (not implemented yet)
        """
        self.log_path = Path(log_path)
        self.max_buffer_size = max_buffer_size
        self.auto_flush_interval = auto_flush_interval

        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread-safe buffer
        self._buffer = []
        self._lock = threading.Lock()
        self._closed = False

    def record_event(self, event: TelemetryEvent) -> None:
        """Record an event, flushing if buffer is full.

        Args:
            event: TelemetryEvent to record
        """
        if self._closed:
            return

        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= self.max_buffer_size:
                self._flush_unlocked()

    def flush(self) -> None:
        """Flush buffered events to disk."""
        with self._lock:
            self._flush_unlocked()

    def _flush_unlocked(self) -> None:
        """Internal flush (assumes lock is already held)."""
        if not self._buffer or self._closed:
            return

        try:
            with open(self.log_path, "a") as f:
                for event in self._buffer:
                    json_str = json.dumps(event.to_dict(), default=str)
                    f.write(json_str + "\n")
            self._buffer.clear()
        except IOError as e:
            print(f"Error writing telemetry to {self.log_path}: {e}")

    def close(self) -> None:
        """Close recorder and flush remaining events."""
        with self._lock:
            if not self._closed:
                self._flush_unlocked()
                self._closed = True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit; flush and close."""
        self.close()

    @classmethod
    def for_queue(
        cls, queue_id: str, log_root: Optional[Path] = None, timestamp: Optional[datetime] = None
    ) -> "TelemetryRecorder":
        """Factory method to create recorder for a queue execution.

        Creates a log file in {log_root}/telemetry/ with name:
            queue_{queue_id}_{timestamp}.jsonl

        Args:
            queue_id: Experiment/queue name (e.g., "experiment_001")
            log_root: Root directory for logs (defaults to ~/.pychron.APP_ID/logs/)
            timestamp: Timestamp for filename (defaults to now)

        Returns:
            TelemetryRecorder instance
        """
        if log_root is None:
            # Try to use pychron's default log directory
            from pychron.paths import paths

            log_root = Path(paths.log_dir)
        else:
            log_root = Path(log_root)

        if timestamp is None:
            timestamp = datetime.now()

        # Create telemetry subdirectory
        telemetry_dir = log_root / "telemetry"
        telemetry_dir.mkdir(parents=True, exist_ok=True)

        # Format timestamp for filename
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"queue_{queue_id}_{ts_str}.jsonl"
        log_path = telemetry_dir / filename

        return cls(log_path)

    @classmethod
    def for_run(
        cls,
        run_id: str,
        queue_id: str,
        log_root: Optional[Path] = None,
        timestamp: Optional[datetime] = None,
    ) -> "TelemetryRecorder":
        """Factory method to create recorder for a single run.

        Creates a log file in {log_root}/telemetry/ with name:
            run_{run_id}_{timestamp}.jsonl

        Args:
            run_id: Run ID
            queue_id: Parent queue ID
            log_root: Root directory for logs (defaults to ~/.pychron.APP_ID/logs/)
            timestamp: Timestamp for filename (defaults to now)

        Returns:
            TelemetryRecorder instance
        """
        if log_root is None:
            from pychron.paths import paths

            log_root = Path(paths.log_dir)
        else:
            log_root = Path(log_root)

        if timestamp is None:
            timestamp = datetime.now()

        telemetry_dir = log_root / "telemetry"
        telemetry_dir.mkdir(parents=True, exist_ok=True)

        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"run_{run_id}_{ts_str}.jsonl"
        log_path = telemetry_dir / filename

        return cls(log_path)
