# ===============================================================================
# Copyright 2024 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

"""
Hardware library filtering and search capabilities.

Provides advanced search and filtering across discovered hardware drivers.
"""

import re
from typing import List, Optional, Tuple

from traits.api import HasTraits, Str, on_trait_change
from traitsui.api import View, Item, HGroup, VGroup

from pychron.hardware.library import LibraryEntry


class LibraryFilter(HasTraits):
    """
    Filter criteria for hardware device library.

    Supports:
    - Full-text search across metadata
    - Filtering by company, communication type, completeness
    """

    search_text = Str("")
    company_filter = Str("")
    comm_type_filter = Str("")
    completeness_filter = Str("")  # 'all', 'complete', 'incomplete'

    def traits_view(self):
        """Define the traitsUI view for LibraryFilter."""
        return View(
            VGroup(
                Item("search_text", label="Search"),
                HGroup(
                    Item("company_filter", label="Company"),
                    Item("comm_type_filter", label="Comm Type"),
                    Item("completeness_filter", label="Status"),
                ),
            )
        )

    def matches(self, entry: LibraryEntry) -> bool:
        """
        Check if entry matches all filter criteria.

        Args:
            entry: LibraryEntry to test

        Returns:
            True if entry passes all filters, False otherwise
        """
        # Check completeness filter
        if self.completeness_filter == "complete" and not entry.is_complete:
            return False
        if self.completeness_filter == "incomplete" and entry.is_complete:
            return False

        # Check company filter
        if self.company_filter and self.company_filter.lower() not in entry.company.lower():
            return False

        # Check communication type filter
        if (
            self.comm_type_filter
            and self.comm_type_filter.lower() != entry.default_comm_type.lower()
        ):
            return False

        # Check search text (full-text search)
        if self.search_text:
            return self._full_text_search(entry, self.search_text)

        return True

    def _full_text_search(self, entry: LibraryEntry, query: str) -> bool:
        """
        Perform full-text search across entry metadata.

        Searches:
        - Name, description, company
        - Class name, model, part number
        - All custom metadata fields

        Args:
            entry: Entry to search
            query: Search query (case-insensitive regex)

        Returns:
            True if query matches any field
        """
        query_lower = query.lower()
        query_regex = re.compile(query_lower, re.IGNORECASE)

        # Search standard fields
        search_fields = [
            entry.name,
            entry.description,
            entry.company,
            entry.class_name,
            entry.model or "",
            entry.vendor_part_number or "",
        ]

        for field_value in search_fields:
            if query_regex.search(str(field_value)):
                return True

        # Search all metadata
        for key, value in entry.metadata.items():
            if query_regex.search(f"{key} {value}"):
                return True

        return False

    def reset(self) -> None:
        """Reset all filters to default (match all)."""
        self.search_text = ""
        self.company_filter = ""
        self.comm_type_filter = ""
        self.completeness_filter = ""


class LibrarySearcher:
    """Helper class for searching and filtering library entries."""

    @staticmethod
    def filter_entries(
        entries: List[LibraryEntry], filter_criteria: LibraryFilter
    ) -> List[LibraryEntry]:
        """
        Filter list of entries using filter criteria.

        Args:
            entries: List of LibraryEntry objects
            filter_criteria: LibraryFilter with search/filter settings

        Returns:
            Filtered list of entries
        """
        return [e for e in entries if filter_criteria.matches(e)]

    @staticmethod
    def get_unique_companies(entries: List[LibraryEntry]) -> List[str]:
        """
        Get sorted list of unique company names from entries.

        Args:
            entries: List of LibraryEntry objects

        Returns:
            Sorted list of unique company names (excluding empty)
        """
        companies = set(e.company for e in entries if e.company)
        return sorted(companies)

    @staticmethod
    def get_unique_comm_types(entries: List[LibraryEntry]) -> List[str]:
        """
        Get sorted list of unique communication types from entries.

        Args:
            entries: List of LibraryEntry objects

        Returns:
            Sorted list of unique communication types
        """
        comm_types = set(e.default_comm_type for e in entries)
        return sorted(comm_types)

    @staticmethod
    def get_completeness_stats(entries: List[LibraryEntry]) -> Tuple[int, int, float]:
        """
        Get completeness statistics for entries.

        Args:
            entries: List of LibraryEntry objects

        Returns:
            Tuple of (total, complete_count, completion_percentage)
        """
        if not entries:
            return 0, 0, 0.0

        complete_count = sum(1 for e in entries if e.is_complete)
        total = len(entries)
        percentage = (complete_count / total) * 100 if total > 0 else 0

        return total, complete_count, percentage

    @staticmethod
    def search_by_text(entries: List[LibraryEntry], query: str) -> List[LibraryEntry]:
        """
        Search entries by text query.

        Args:
            entries: List of LibraryEntry objects
            query: Search query string

        Returns:
            List of matching entries
        """
        filter_obj = LibraryFilter(search_text=query)
        return [e for e in entries if filter_obj._full_text_search(e, query)]

    @staticmethod
    def search_by_company(entries: List[LibraryEntry], company: str) -> List[LibraryEntry]:
        """
        Search entries by company name.

        Args:
            entries: List of LibraryEntry objects
            company: Company name (partial match, case-insensitive)

        Returns:
            List of matching entries
        """
        company_lower = company.lower()
        return [e for e in entries if company_lower in e.company.lower()]

    @staticmethod
    def search_by_comm_type(entries: List[LibraryEntry], comm_type: str) -> List[LibraryEntry]:
        """
        Search entries by communication type.

        Args:
            entries: List of LibraryEntry objects
            comm_type: Communication type ('ethernet' or 'serial')

        Returns:
            List of matching entries
        """
        comm_type_lower = comm_type.lower()
        return [e for e in entries if comm_type_lower == e.default_comm_type.lower()]

    @staticmethod
    def search_incomplete(entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """
        Get all incomplete entries (missing required metadata).

        Args:
            entries: List of LibraryEntry objects

        Returns:
            List of incomplete entries
        """
        return [e for e in entries if not e.is_complete]


# ============= EOF =============================================
