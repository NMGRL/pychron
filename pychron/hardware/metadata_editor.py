"""In-app metadata editor for hardware library entries.

This module provides functionality to edit device metadata in the UI
with validation before saving back to source files.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class EditSession:
    """Represents an active metadata editing session.

    Attributes:
        entry_name: Name of entry being edited
        original_metadata: Copy of original metadata
        edited_metadata: Current edited metadata
        changes_made: Dict of field -> (old_value, new_value)
        validation_errors: List of validation error messages
        start_time: When editing session started
    """

    entry_name: str
    original_metadata: Dict[str, Any]
    edited_metadata: Dict[str, Any] = field(default_factory=dict)
    changes_made: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)
    validation_errors: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

    def has_changes(self) -> bool:
        """Check if any changes have been made."""
        return len(self.changes_made) > 0

    def track_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Track a field change.

        Args:
            field: Field name
            old_value: Original value
            new_value: New value
        """
        if old_value == new_value:
            # Remove tracking if reverted to original
            self.changes_made.pop(field, None)
        else:
            self.changes_made[field] = (old_value, new_value)

    def get_changeset(self) -> Dict[str, Tuple[Any, Any]]:
        """Get all tracked changes.

        Returns:
            Dict of field -> (old, new) tuples
        """
        return dict(self.changes_made)

    def revert(self) -> None:
        """Revert all changes to original values."""
        self.edited_metadata = dict(self.original_metadata)
        self.changes_made.clear()
        self.validation_errors.clear()


class MetadataEditor:
    """Editor for device metadata with validation.

    Handles editing metadata for library entries with validation
    and change tracking before persisting to source files.
    """

    # Define editable fields and their types
    EDITABLE_FIELDS = {
        "name": str,
        "description": str,
        "company": str,
        "model": str,
        "vendor_part_number": str,
        "default_comm_type": str,
        "docs_url": str,
        "website": str,
    }

    # Define required fields that must have values
    REQUIRED_FIELDS = {
        "name": "Device name",
        "description": "Description",
        "company": "Manufacturer",
        "default_comm_type": "Communication type",
    }

    # Define field validation rules
    VALIDATION_RULES = {
        "docs_url": ("url", "Must be a valid URL or empty"),
        "website": ("url", "Must be a valid URL or empty"),
        "name": ("non_empty", "Name cannot be empty"),
        "description": ("non_empty", "Description cannot be empty"),
        "company": ("non_empty", "Company cannot be empty"),
    }

    def __init__(self) -> None:
        """Initialize metadata editor."""
        self.current_session: Optional[EditSession] = None

    def begin_edit(self, entry: Any) -> EditSession:
        """Start editing metadata for an entry.

        Args:
            entry: LibraryEntry to edit

        Returns:
            EditSession for tracking changes

        Raises:
            ValueError: If entry cannot be edited
        """
        if not hasattr(entry, "metadata"):
            raise ValueError("Entry does not have metadata attribute")

        # Create copy of original metadata
        original = dict(entry.metadata) if entry.metadata else {}

        session = EditSession(
            entry_name=entry.name,
            original_metadata=original,
            edited_metadata=dict(original),
        )

        self.current_session = session
        logger.info(f"Started editing metadata for: {entry.name}")
        return session

    def set_field(self, field: str, value: Any) -> bool:
        """Set a metadata field value.

        Args:
            field: Field name to set
            value: New value

        Returns:
            True if field was set, False if validation failed

        Raises:
            RuntimeError: If no active editing session
        """
        if not self.current_session:
            raise RuntimeError("No active editing session")

        if field not in self.EDITABLE_FIELDS:
            logger.warning(f"Attempt to edit non-editable field: {field}")
            return False

        old_value = self.current_session.edited_metadata.get(field)

        # Validate before setting
        validation_result = self._validate_field(field, value)
        if not validation_result.is_valid:
            logger.warning(f"Validation failed for {field}: {validation_result.errors}")
            return False

        self.current_session.edited_metadata[field] = value
        self.current_session.track_change(field, old_value, value)
        return True

    def get_field(self, field: str) -> Any:
        """Get current value of a field.

        Args:
            field: Field name

        Returns:
            Current value in editing session

        Raises:
            RuntimeError: If no active editing session
        """
        if not self.current_session:
            raise RuntimeError("No active editing session")

        return self.current_session.edited_metadata.get(field)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate all edited metadata.

        Returns:
            Tuple of (is_valid, error_messages)

        Raises:
            RuntimeError: If no active editing session
        """
        if not self.current_session:
            raise RuntimeError("No active editing session")

        errors = []

        # Check required fields
        for field, label in self.REQUIRED_FIELDS.items():
            value = self.current_session.edited_metadata.get(field, "").strip()
            if not value:
                errors.append(f"{label} is required")

        # Validate each field
        for field, value in self.current_session.edited_metadata.items():
            validation_result = self._validate_field(field, value)
            if not validation_result.is_valid:
                errors.extend(validation_result.errors)

        self.current_session.validation_errors = errors
        return len(errors) == 0, errors

    @dataclass
    class ValidationResult:
        """Result of field validation."""

        is_valid: bool
        errors: List[str] = field(default_factory=list)

    def _validate_field(self, field: str, value: Any) -> "MetadataEditor.ValidationResult":
        """Validate a single field.

        Args:
            field: Field name
            value: Value to validate

        Returns:
            ValidationResult with validation status
        """
        if field not in self.VALIDATION_RULES:
            # No validation rules for this field
            return self.ValidationResult(is_valid=True)

        rule_type, error_msg = self.VALIDATION_RULES[field]

        if rule_type == "url":
            if value and not value.strip().startswith(("http://", "https://")):
                return self.ValidationResult(is_valid=False, errors=[error_msg])

        elif rule_type == "non_empty":
            if not value or (isinstance(value, str) and not value.strip()):
                return self.ValidationResult(is_valid=False, errors=[error_msg])

        return self.ValidationResult(is_valid=True)

    def save_changes(self, entry: Any) -> bool:
        """Save edited metadata back to entry.

        Args:
            entry: LibraryEntry to update

        Returns:
            True if save succeeded, False otherwise

        Raises:
            RuntimeError: If no active editing session
        """
        if not self.current_session:
            raise RuntimeError("No active editing session")

        # Validate before saving
        is_valid, errors = self.validate()
        if not is_valid:
            logger.warning(f"Validation failed: {errors}")
            return False

        try:
            # Update entry metadata
            if not hasattr(entry, "metadata"):
                entry.metadata = {}

            for field, value in self.current_session.edited_metadata.items():
                entry.metadata[field] = value

            logger.info(
                f"Saved metadata changes for {entry.name}: "
                f"{len(self.current_session.changes_made)} field(s) updated"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            return False

    def cancel_edit(self) -> None:
        """Cancel current editing session.

        Raises:
            RuntimeError: If no active editing session
        """
        if not self.current_session:
            raise RuntimeError("No active editing session")

        session_name = self.current_session.entry_name
        self.current_session = None
        logger.info(f"Cancelled editing for: {session_name}")

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current editing session.

        Returns:
            Dict with session info or None if no active session
        """
        if not self.current_session:
            return None

        return {
            "entry_name": self.current_session.entry_name,
            "has_changes": self.current_session.has_changes(),
            "changes_count": len(self.current_session.changes_made),
            "validation_errors": self.current_session.validation_errors,
            "changeset": self.current_session.get_changeset(),
        }

    def get_changes_summary(self) -> str:
        """Get summary of changes in current session.

        Returns:
            String summary of changes

        Raises:
            RuntimeError: If no active editing session
        """
        if not self.current_session:
            raise RuntimeError("No active editing session")

        if not self.current_session.has_changes():
            return "No changes made"

        lines = [f"Changes to {self.current_session.entry_name}:"]
        for field, (old, new) in self.current_session.changes_made.items():
            lines.append(f"  {field}: '{old}' -> '{new}'")

        return "\n".join(lines)

    @staticmethod
    def get_field_display_name(field: str) -> str:
        """Get user-friendly display name for a field.

        Args:
            field: Field name

        Returns:
            Display name
        """
        display_names = {
            "name": "Device Name",
            "description": "Description",
            "company": "Manufacturer",
            "model": "Model",
            "vendor_part_number": "Part Number",
            "default_comm_type": "Communication Type",
            "docs_url": "Documentation URL",
            "website": "Website",
        }
        return display_names.get(field, field.replace("_", " ").title())

    @staticmethod
    def get_field_type(field: str) -> type:
        """Get the expected type for a field.

        Args:
            field: Field name

        Returns:
            Field type
        """
        return MetadataEditor.EDITABLE_FIELDS.get(field, str)
