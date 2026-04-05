"""Export utilities for Prometheus events."""

import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class EventExporter:
    """Utility for exporting Prometheus events to various formats."""

    @staticmethod
    def export_to_file(
        events_data: str, format_type: str = "json", filename: Optional[str] = None
    ) -> Optional[Path]:
        """Export events to a file.

        Args:
            events_data: Formatted event data (JSON or CSV string)
            format_type: Export format ("json" or "csv")
            filename: Optional custom filename (without extension)

        Returns:
            Path to exported file, or None if export failed
        """
        try:
            # Determine file extension
            ext = ".json" if format_type == "json" else ".csv"

            # Create temp file with appropriate naming
            if filename:
                filepath = Path(tempfile.gettempdir()) / f"{filename}{ext}"
            else:
                suffix = ext
                with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
                    filepath = Path(f.name)

            # Write data to file
            filepath.write_text(events_data)
            logger.info(f"Events exported to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to export events: {e}")
            return None

    @staticmethod
    def open_export_dialog(events_data: str, format_type: str = "json") -> Optional[Path]:
        """Open a file save dialog and export events.

        Args:
            events_data: Formatted event data
            format_type: Export format

        Returns:
            Path to saved file, or None if cancelled
        """
        try:
            from pyface.api import FileDialog, OK

            ext = "json" if format_type == "json" else "csv"
            wildcard = f"*.{ext}|*.{ext} files|*.*|All files"

            dialog = FileDialog(
                title="Export Events",
                action="save as",
                wildcard=wildcard,
                default_suffix=f".{ext}",
            )

            if dialog.open() == OK:
                filepath = Path(dialog.path)
                filepath.write_text(events_data)
                logger.info(f"Events exported to {filepath}")
                return filepath
            else:
                logger.info("Export cancelled by user")
                return None

        except Exception as e:
            logger.error(f"Failed to open export dialog: {e}")
            return None

    @staticmethod
    def get_export_summary(events_count: int, filepath: Optional[Path]) -> str:
        """Generate a summary message for export operation.

        Args:
            events_count: Number of events exported
            filepath: Path to exported file

        Returns:
            Summary message
        """
        if filepath:
            return f"Exported {events_count} events to {filepath.name}"
        else:
            return f"Failed to export {events_count} events"
