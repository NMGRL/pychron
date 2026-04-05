"""Metadata validation and reporting for hardware library.

This module provides validation functionality for device metadata,
generating reports on completeness and missing fields.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Report on metadata completeness and issues.

    Attributes:
        total_entries: Total number of library entries
        complete_entries: Number of entries with all required fields
        incomplete_entries: Number of entries missing required fields
        missing_fields_by_entry: Dict mapping entry names to lists of missing fields
        required_fields: List of fields considered required
        generated_at: Timestamp when report was generated
    """

    total_entries: int
    complete_entries: int
    incomplete_entries: int
    missing_fields_by_entry: Dict[str, List[str]]
    required_fields: List[str] = field(
        default_factory=lambda: [
            "name",
            "class_name",
            "description",
            "company",
            "default_comm_type",
        ]
    )
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def completion_percentage(self) -> float:
        """Calculate overall completion percentage."""
        if self.total_entries == 0:
            return 0.0
        return (self.complete_entries / self.total_entries) * 100

    @property
    def most_missing_field(self) -> Optional[str]:
        """Get the field most frequently missing."""
        if not self.missing_fields_by_entry:
            return None

        field_counts: Dict[str, int] = {}
        for missing in self.missing_fields_by_entry.values():
            for field_name in missing:
                field_counts[field_name] = field_counts.get(field_name, 0) + 1

        if not field_counts:
            return None
        return max(field_counts, key=field_counts.get)

    @property
    def incomplete_entries_sorted(self) -> List[tuple]:
        """Get incomplete entries sorted by number of missing fields."""
        items = [(name, len(fields)) for name, fields in self.missing_fields_by_entry.items()]
        return sorted(items, key=lambda x: x[1], reverse=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "total_entries": self.total_entries,
            "complete_entries": self.complete_entries,
            "incomplete_entries": self.incomplete_entries,
            "completion_percentage": self.completion_percentage,
            "missing_fields_by_entry": self.missing_fields_by_entry,
            "required_fields": self.required_fields,
            "generated_at": self.generated_at.isoformat(),
        }

    def to_html(self, title: str = "Metadata Validation Report") -> str:
        """Generate HTML report.

        Args:
            title: Report title

        Returns:
            HTML string
        """
        percentage = self.completion_percentage
        color = "green" if percentage >= 90 else "orange" if percentage >= 70 else "red"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .summary {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
        .stat {{ display: inline-block; margin-right: 30px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: {color}; }}
        .stat-label {{ font-size: 12px; color: #666; }}
        .chart {{ margin: 20px 0; }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            width: {percentage}%;
            background: {color};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
        th {{ background: #f5f5f5; font-weight: bold; }}
        tr:hover {{ background: #f9f9f9; }}
        .incomplete {{ color: #d32f2f; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="stat">
            <div class="stat-value">{self.complete_entries}/{self.total_entries}</div>
            <div class="stat-label">Complete Entries</div>
        </div>
        <div class="stat">
            <div class="stat-value">{self.incomplete_entries}</div>
            <div class="stat-label">Incomplete Entries</div>
        </div>
        <div class="stat">
            <div class="stat-value">{percentage:.1f}%</div>
            <div class="stat-label">Completion</div>
        </div>
    </div>

    <div class="chart">
        <h3>Completion Progress</h3>
        <div class="progress-bar">
            <div class="progress-fill">{percentage:.1f}%</div>
        </div>
    </div>

    <div>
        <h3>Incomplete Entries</h3>
        <table>
            <tr>
                <th>Entry Name</th>
                <th>Missing Fields</th>
                <th>Field Count</th>
            </tr>
"""

        for name, missing_fields in self.incomplete_entries_sorted[:20]:
            html += f"""            <tr>
                <td><span class="incomplete">{name}</span></td>
                <td>{", ".join(missing_fields)}</td>
                <td>{len(missing_fields)}</td>
            </tr>
"""

        html += """        </table>
    </div>

    <div class="footer">
        <p>This report was automatically generated. Review and update metadata as needed.</p>
    </div>
</body>
</html>
"""
        return html

    def to_csv(self) -> str:
        """Generate CSV format report.

        Returns:
            CSV string
        """
        lines = [
            "Entry Name,Missing Fields,Field Count",
        ]

        for name, missing_fields in self.incomplete_entries_sorted:
            missing_str = ";".join(missing_fields)
            lines.append(f'"{name}","{missing_str}",{len(missing_fields)}')

        return "\n".join(lines)


class MetadataValidator:
    """Validator for hardware library metadata."""

    # Define required fields for different entry types
    REQUIRED_FIELDS = [
        "name",
        "class_name",
        "description",
        "company",
        "default_comm_type",
    ]

    # Optional fields that should be present for complete entries
    RECOMMENDED_FIELDS = [
        "docs_url",
        "website",
        "model",
        "vendor_part_number",
    ]

    @staticmethod
    def validate_entry(entry: Any) -> tuple[bool, List[str]]:
        """Validate a single library entry.

        Args:
            entry: LibraryEntry to validate

        Returns:
            Tuple of (is_valid, missing_fields_list)
        """
        missing = []

        for field in MetadataValidator.REQUIRED_FIELDS:
            value = getattr(entry, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(field)

        is_valid = len(missing) == 0
        return is_valid, missing

    @staticmethod
    def generate_report(entries: List[Any]) -> ValidationReport:
        """Generate validation report for library entries.

        Args:
            entries: List of LibraryEntry instances

        Returns:
            ValidationReport with completeness analysis
        """
        if not entries:
            return ValidationReport(
                total_entries=0,
                complete_entries=0,
                incomplete_entries=0,
                missing_fields_by_entry={},
            )

        complete_count = 0
        incomplete_count = 0
        missing_by_entry = {}

        for entry in entries:
            is_valid, missing_fields = MetadataValidator.validate_entry(entry)

            if is_valid:
                complete_count += 1
            else:
                incomplete_count += 1
                missing_by_entry[entry.name] = missing_fields

        report = ValidationReport(
            total_entries=len(entries),
            complete_entries=complete_count,
            incomplete_entries=incomplete_count,
            missing_fields_by_entry=missing_by_entry,
        )

        logger.info(
            f"Validation report: {complete_count}/{len(entries)} complete "
            f"({report.completion_percentage:.1f}%)"
        )

        return report

    @staticmethod
    def export_report(report: ValidationReport, output_path: Path, format: str = "html") -> bool:
        """Export validation report to file.

        Args:
            report: ValidationReport to export
            output_path: Path where report will be written
            format: Output format ('html' or 'csv')

        Returns:
            True if export succeeded, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format == "html":
                content = report.to_html()
                output_path = output_path.with_suffix(".html")
            elif format == "csv":
                content = report.to_csv()
                output_path = output_path.with_suffix(".csv")
            else:
                logger.error(f"Unknown format: {format}")
                return False

            with open(output_path, "w") as f:
                f.write(content)

            logger.info(f"Exported validation report to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False

    @staticmethod
    def get_missing_fields_summary(report: ValidationReport) -> Dict[str, int]:
        """Get summary of which fields are missing most frequently.

        Args:
            report: ValidationReport to analyze

        Returns:
            Dict mapping field names to count of occurrences
        """
        field_counts: Dict[str, int] = {}

        for missing_fields in report.missing_fields_by_entry.values():
            for field in missing_fields:
                field_counts[field] = field_counts.get(field, 0) + 1

        # Sort by count descending
        return dict(sorted(field_counts.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def suggest_improvements(report: ValidationReport) -> List[str]:
        """Generate list of improvement suggestions.

        Args:
            report: ValidationReport to analyze

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if report.completion_percentage < 50:
            suggestions.append(
                "Critical: Less than 50% of entries are complete. " "Prioritize metadata updates."
            )
        elif report.completion_percentage < 75:
            suggestions.append(
                "Moderate: Less than 75% of entries are complete. " "Update incomplete entries."
            )

        # Find most problematic field
        field_summary = MetadataValidator.get_missing_fields_summary(report)
        if field_summary:
            most_missing = list(field_summary.keys())[0]
            count = field_summary[most_missing]
            suggestions.append(
                f"Most common missing field: '{most_missing}' ({count} entries). "
                f"Add this field where applicable."
            )

        # Check for entries with many missing fields
        entries_with_many_missing = [
            (name, len(fields))
            for name, fields in report.missing_fields_by_entry.items()
            if len(fields) >= 3
        ]
        if entries_with_many_missing:
            worst = max(entries_with_many_missing, key=lambda x: x[1])
            suggestions.append(
                f"Priority: Entry '{worst[0]}' has {worst[1]} missing fields. "
                f"Consider adding a full metadata template for this entry."
            )

        return suggestions
