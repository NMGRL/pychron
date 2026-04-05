from __future__ import annotations

import csv
import math
import re
from contextlib import nullcontext
from dataclasses import dataclass
from io import StringIO
from typing import Any, Iterable

from traits.api import HasTraits, Dict, Enum, Int, List, Property, Str, cached_property

CANONICAL_FIELDS = (
    "sample",
    "material",
    "grainsize",
    "project",
    "principal_investigator",
    "latitude",
    "longitude",
    "easting",
    "northing",
    "utm",
    "unit",
    "igsn",
    "storage_location",
    "lithology",
    "location",
    "approximate_age",
    "elevation",
    "note",
)
REQUIRED_FIELDS = ("sample", "project", "principal_investigator", "material")
ACTION_LABELS = ("All", "Create", "Skip", "Error")

FIELD_ALIASES = {
    "sample": ("name", "sample_name"),
    "material": ("mineral",),
    "grainsize": ("grain_size", "grain"),
    "project": ("project_name",),
    "principal_investigator": ("pi", "principalinvestigator", "principal investigator"),
    "latitude": ("lat",),
    "longitude": ("lon", "long"),
    "easting": ("e", "utm_e", "utm e"),
    "northing": ("n", "utm_n", "utm n"),
    "utm": ("zone", "utm_zone", "utm zone"),
    "unit": tuple(),
    "igsn": tuple(),
    "storage_location": ("storage",),
    "lithology": tuple(),
    "location": tuple(),
    "approximate_age": ("age", "approx_age"),
    "elevation": tuple(),
    "note": ("comment", "comments", "notes"),
}

_NORMALIZE_REGEX = re.compile(r"[^a-z0-9]+")
_UTM_REGEX = re.compile(r"^\s*(?P<zone>\d{1,2})(?P<band>[A-Za-z]?)\s*$")


def normalize_header(value: str) -> str:
    return _NORMALIZE_REGEX.sub("_", value.strip().lower()).strip("_")


_ALIAS_LOOKUP = {}
for _field in CANONICAL_FIELDS:
    _ALIAS_LOOKUP[normalize_header(_field)] = _field
    for _alias in FIELD_ALIASES.get(_field, tuple()):
        _ALIAS_LOOKUP[normalize_header(_alias)] = _field


class ImportIssue(HasTraits):
    row = Int
    field = Str
    severity = Enum("warning", "error")
    code = Str
    message = Str


class MappingItem(HasTraits):
    source_header = Str
    target_field = Enum(*([""] + list(CANONICAL_FIELDS)))


class SampleImportRow(HasTraits):
    source_row_index = Int
    sample = Str
    material = Str
    grainsize = Str
    project = Str
    principal_investigator = Str
    latitude_text = Str
    longitude_text = Str
    easting_text = Str
    northing_text = Str
    utm_text = Str
    unit = Str
    igsn = Str
    storage_location = Str
    lithology = Str
    location = Str
    approximate_age_text = Str
    elevation_text = Str
    note = Str
    action = Str("error")
    raw = Dict(Str, Str)
    issues = List(ImportIssue)

    latitude = None
    longitude = None
    approximate_age = None
    elevation = None

    status_text = Property(depends_on="action, issues_items")
    error_messages = Property(depends_on="issues_items")
    warning_messages = Property(depends_on="issues_items")

    def add_issue(self, severity: str, code: str, message: str, field: str = "") -> None:
        self.issues.append(
            ImportIssue(
                row=self.source_row_index,
                field=field,
                severity=severity,
                code=code,
                message=message,
            )
        )

    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def normalized_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.sample.strip().lower(),
            self.project.strip().lower(),
            self.principal_investigator.strip().lower(),
            self.material.strip().lower(),
            self.grainsize.strip().lower(),
        )

    @cached_property
    def _get_status_text(self) -> str:
        if self.error_messages:
            return self.error_messages
        if self.warning_messages:
            return self.warning_messages
        return self.action.capitalize()

    @cached_property
    def _get_error_messages(self) -> str:
        return "; ".join(issue.message for issue in self.issues if issue.severity == "error")

    @cached_property
    def _get_warning_messages(self) -> str:
        return "; ".join(issue.message for issue in self.issues if issue.severity == "warning")


class SampleImportPreview(HasTraits):
    delimiter = Str(",")
    headers = List(Str)
    rows = List(SampleImportRow)
    parse_errors = List(Str)

    row_count = Property(depends_on="rows_items")
    create_count = Property(depends_on="rows_items")
    skip_count = Property(depends_on="rows_items")
    error_count = Property(depends_on="rows_items")
    summary_text = Property(depends_on="rows_items, parse_errors_items")

    def rows_for_action(self, action: str) -> list[SampleImportRow]:
        if action == "All":
            return list(self.rows)
        target = action.lower()
        return [row for row in self.rows if row.action == target]

    def error_rows(self) -> list[SampleImportRow]:
        return [row for row in self.rows if row.action == "error"]

    def create_rows(self) -> list[SampleImportRow]:
        return [row for row in self.rows if row.action == "create"]

    @cached_property
    def _get_row_count(self) -> int:
        return len(self.rows)

    @cached_property
    def _get_create_count(self) -> int:
        return len(self.create_rows())

    @cached_property
    def _get_skip_count(self) -> int:
        return len(self.rows_for_action("Skip"))

    @cached_property
    def _get_error_count(self) -> int:
        return len(self.error_rows())

    @cached_property
    def _get_summary_text(self) -> str:
        parts = [
            "Rows: {}".format(self.row_count),
            "Creates: {}".format(self.create_count),
            "Skips: {}".format(self.skip_count),
            "Errors: {}".format(self.error_count),
        ]
        if self.parse_errors:
            parts.append("Parse: {}".format("; ".join(self.parse_errors)))
        return " | ".join(parts)


@dataclass
class ParsedCSV:
    delimiter: str
    headers: list[str]
    raw_rows: list[tuple[int, dict[str, str]]]
    errors: list[str]


class SampleImportService:
    def __init__(self, dvc: Any | None = None):
        self.dvc = dvc

    @property
    def template_fields(self) -> tuple[str, ...]:
        return CANONICAL_FIELDS

    def build_mappings(self, headers: Iterable[str]) -> list[MappingItem]:
        used: set[str] = set()
        mappings: list[MappingItem] = []
        for header in headers:
            target = _ALIAS_LOOKUP.get(normalize_header(header), "")
            if target and target in used:
                target = ""
            if target:
                used.add(target)
            mappings.append(MappingItem(source_header=header, target_field=target))
        return mappings

    def parse_csv(self, path: str) -> ParsedCSV:
        errors: list[str] = []
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as rfile:
                text = rfile.read()
        except (OSError, UnicodeDecodeError) as exc:
            return ParsedCSV(",", [], [], [str(exc)])

        if not text.strip():
            return ParsedCSV(",", [], [], ["File is empty"])

        delimiter = self._detect_delimiter(text)
        reader = csv.reader(StringIO(text), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return ParsedCSV(delimiter, [], [], ["File is empty"])

        headers = [header.strip() for header in rows[0]]
        if not any(headers):
            errors.append("Header row is empty")
            return ParsedCSV(delimiter, headers, [], errors)

        if len(set(headers)) != len(headers):
            errors.append("Header row contains duplicate column names")

        raw_rows: list[tuple[int, dict[str, str]]] = []
        for idx, values in enumerate(rows[1:], start=2):
            if not any(value.strip() for value in values):
                continue
            row = {}
            for ci, header in enumerate(headers):
                row[header] = values[ci].strip() if ci < len(values) else ""
            raw_rows.append((idx, row))

        return ParsedCSV(delimiter, headers, raw_rows, errors)

    def preview(
        self, path: str, mappings: Iterable[MappingItem] | None = None
    ) -> SampleImportPreview:
        parsed = self.parse_csv(path)
        mapping_items = (
            list(mappings) if mappings is not None else self.build_mappings(parsed.headers)
        )
        rows = [self._map_row(index, raw, mapping_items) for index, raw in parsed.raw_rows]
        self._validate_rows(rows)
        return SampleImportPreview(
            delimiter=parsed.delimiter,
            headers=parsed.headers,
            rows=rows,
            parse_errors=parsed.errors,
        )

    def export_rows(
        self, path: str, rows: Iterable[SampleImportRow], headers: Iterable[str]
    ) -> None:
        ordered_headers = list(headers)
        with open(path, "w", encoding="utf-8", newline="") as wfile:
            writer = csv.DictWriter(
                wfile,
                fieldnames=ordered_headers + ["row_action", "error_messages", "warning_messages"],
            )
            writer.writeheader()
            for row in rows:
                payload = {header: row.raw.get(header, "") for header in ordered_headers}
                payload["row_action"] = row.action
                payload["error_messages"] = row.error_messages
                payload["warning_messages"] = row.warning_messages
                writer.writerow(payload)

    def _detect_delimiter(self, text: str) -> str:
        try:
            dialect = csv.Sniffer().sniff(text[:2048], delimiters=",;\t|")
            return dialect.delimiter
        except csv.Error:
            return ","

    def _map_row(
        self, row_index: int, raw: dict[str, str], mappings: Iterable[MappingItem]
    ) -> SampleImportRow:
        mapped = {
            mapping.target_field: raw.get(mapping.source_header, "")
            for mapping in mappings
            if mapping.target_field
        }
        row = SampleImportRow(
            source_row_index=row_index,
            sample=mapped.get("sample", "").strip(),
            material=mapped.get("material", "").strip(),
            grainsize=mapped.get("grainsize", "").strip(),
            project=mapped.get("project", "").strip(),
            principal_investigator=mapped.get("principal_investigator", "").strip(),
            latitude_text=mapped.get("latitude", "").strip(),
            longitude_text=mapped.get("longitude", "").strip(),
            easting_text=mapped.get("easting", "").strip(),
            northing_text=mapped.get("northing", "").strip(),
            utm_text=mapped.get("utm", "").strip(),
            unit=mapped.get("unit", "").strip(),
            igsn=mapped.get("igsn", "").strip(),
            storage_location=mapped.get("storage_location", "").strip(),
            lithology=mapped.get("lithology", "").strip(),
            location=mapped.get("location", "").strip(),
            approximate_age_text=mapped.get("approximate_age", "").strip(),
            elevation_text=mapped.get("elevation", "").strip(),
            note=mapped.get("note", "").strip(),
            raw=raw,
        )
        row.latitude = self._coerce_float(row, "latitude", row.latitude_text)
        row.longitude = self._coerce_float(row, "longitude", row.longitude_text)
        row.approximate_age = self._coerce_float(row, "approximate_age", row.approximate_age_text)
        row.elevation = self._coerce_float(row, "elevation", row.elevation_text)
        return row

    def _validate_rows(self, rows: list[SampleImportRow]) -> None:
        seen: dict[tuple[str, str, str, str, str], list[SampleImportRow]] = {}
        for row in rows:
            for field in REQUIRED_FIELDS:
                if not getattr(row, field):
                    row.add_issue(
                        "error",
                        "missing_required",
                        "{} is required".format(field.replace("_", " ")),
                        field,
                    )

            self._validate_location(row)
            key = row.normalized_key()
            if all(key[:4]):
                seen.setdefault(key, []).append(row)

        for dup_rows in seen.values():
            if len(dup_rows) > 1:
                for row in dup_rows:
                    row.add_issue(
                        "error",
                        "duplicate_file_row",
                        "Duplicate sample identity appears in file",
                    )

        with self._session_ctx():
            for row in rows:
                if row.has_errors():
                    row.action = "error"
                    continue

                if self._row_exists(row):
                    row.action = "skip"
                    row.add_issue(
                        "warning",
                        "existing_sample",
                        "Sample already exists and will be skipped",
                    )
                else:
                    row.action = "create"

    def _validate_location(self, row: SampleImportRow) -> None:
        if row.latitude is not None and not -90 <= row.latitude <= 90:
            row.add_issue("error", "invalid_latitude", "Latitude out of range", "latitude")
        if row.longitude is not None and not -180 <= row.longitude <= 180:
            row.add_issue("error", "invalid_longitude", "Longitude out of range", "longitude")

        has_latlon = row.latitude is not None or row.longitude is not None
        has_any_utm = any((row.easting_text, row.northing_text, row.utm_text))
        if has_latlon and (row.latitude is None or row.longitude is None):
            row.add_issue(
                "error",
                "incomplete_latlon",
                "Latitude and longitude must both be provided",
            )

        if has_any_utm:
            if not all((row.easting_text, row.northing_text, row.utm_text)):
                row.add_issue(
                    "error",
                    "incomplete_utm",
                    "UTM requires easting, northing, and utm zone",
                )
            elif row.latitude is not None and row.longitude is not None:
                row.add_issue(
                    "warning",
                    "utm_ignored",
                    "UTM columns ignored because latitude/longitude are present",
                )
            else:
                self._apply_utm(row)

    def _apply_utm(self, row: SampleImportRow) -> None:
        try:
            easting = float(row.easting_text)
            northing = float(row.northing_text)
        except ValueError:
            row.add_issue(
                "error",
                "invalid_utm_value",
                "UTM easting and northing must be numeric",
            )
            return

        match = _UTM_REGEX.match(row.utm_text)
        if not match:
            row.add_issue("error", "invalid_utm_zone", "UTM zone format is invalid")
            return

        zone = int(match.group("zone"))
        band = (match.group("band") or "N").upper()
        south = band < "N"
        try:
            lat, lon = self._utm_to_latlon(easting, northing, zone, south)
        except Exception:
            row.add_issue("error", "utm_conversion_failed", "Failed to convert UTM")
            return

        row.latitude = lat
        row.longitude = lon

    def _coerce_float(self, row: SampleImportRow, field: str, value: str) -> float | None:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            row.add_issue(
                "error",
                "invalid_number",
                "{} must be numeric".format(field.replace("_", " ").capitalize()),
                field,
            )
            return None

    def _row_exists(self, row: SampleImportRow) -> bool:
        if not self.dvc:
            return False
        record = self.dvc.get_sample(
            row.sample,
            row.project,
            row.principal_investigator,
            row.material,
            row.grainsize or None,
        )
        return record is not None

    def _session_ctx(self) -> Any:
        if self.dvc and hasattr(self.dvc, "session_ctx"):
            return self.dvc.session_ctx()
        return nullcontext()

    def _utm_to_latlon(
        self, easting: float, northing: float, zone: int, south: bool
    ) -> tuple[float, float]:
        # Convert WGS84 UTM coordinates without requiring optional GIS packages.
        a = 6378137.0
        ecc_squared = 0.00669438
        k0 = 0.9996

        x = easting - 500000.0
        y = northing
        if south:
            y -= 10000000.0

        long_origin = (zone - 1) * 6 - 180 + 3
        ecc_prime_squared = ecc_squared / (1 - ecc_squared)

        m = y / k0
        mu = m / (a * (1 - ecc_squared / 4 - 3 * ecc_squared**2 / 64 - 5 * ecc_squared**3 / 256))

        e1 = (1 - math.sqrt(1 - ecc_squared)) / (1 + math.sqrt(1 - ecc_squared))
        phi1 = (
            mu
            + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu)
        )

        sin_phi1 = math.sin(phi1)
        cos_phi1 = math.cos(phi1)
        tan_phi1 = math.tan(phi1)

        n1 = a / math.sqrt(1 - ecc_squared * sin_phi1**2)
        t1 = tan_phi1**2
        c1 = ecc_prime_squared * cos_phi1**2
        r1 = a * (1 - ecc_squared) / (1 - ecc_squared * sin_phi1**2) ** 1.5
        d = x / (n1 * k0)

        latitude = phi1 - (
            n1
            * tan_phi1
            / r1
            * (
                d**2 / 2
                - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ecc_prime_squared) * d**4 / 24
                + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ecc_prime_squared - 3 * c1**2)
                * d**6
                / 720
            )
        )
        longitude = (
            d
            - (1 + 2 * t1 + c1) * d**3 / 6
            + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ecc_prime_squared + 24 * t1**2) * d**5 / 120
        ) / cos_phi1

        return math.degrees(latitude), long_origin + math.degrees(longitude)
