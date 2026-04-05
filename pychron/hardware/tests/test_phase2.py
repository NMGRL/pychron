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
Unit tests for Phase 2 UI/UX improvements.

Tests for:
- 2.1 Interactive metadata links
- 2.2 Advanced search & filtering
- 2.3 Enhanced metadata display
"""

import unittest
from pychron.hardware.library import LibraryEntry
from pychron.hardware.library_filter import LibraryFilter, LibrarySearcher


class TestFormattedSpecs(unittest.TestCase):
    """Tests for Phase 2.3: Enhanced metadata display."""

    def setUp(self):
        """Set up test fixtures."""
        self.entry = LibraryEntry(
            class_name="WatlowEZZone",
            package="pychron.hardware.watlow.watlow_ezzone",
            metadata={
                "name": "Watlow EZZone PM",
                "description": "Temperature controller",
                "company": "Watlow",
                "model": "PM-100",
                "vendor_part_number": "ABC-123",
                "default_comm_type": "ethernet",
            },
            is_complete=True,
        )

    def test_formatted_specs_returns_dict(self):
        """Test formatted_specs returns a dictionary."""
        specs = self.entry.formatted_specs

        self.assertIsInstance(specs, dict)
        self.assertIn("Class", specs)
        self.assertIn("Company", specs)
        self.assertIn("Model", specs)

    def test_formatted_specs_contains_all_fields(self):
        """Test formatted_specs includes all expected fields."""
        specs = self.entry.formatted_specs

        expected_keys = [
            "Class",
            "Company",
            "Model",
            "Part Number",
            "Comm Type",
            "Status",
        ]
        for key in expected_keys:
            self.assertIn(key, specs)

    def test_formatted_specs_values(self):
        """Test formatted_specs has correct values."""
        specs = self.entry.formatted_specs

        self.assertEqual(specs["Class"], "WatlowEZZone")
        self.assertEqual(specs["Company"], "Watlow")
        self.assertEqual(specs["Model"], "PM-100")
        self.assertEqual(specs["Part Number"], "ABC-123")
        self.assertEqual(specs["Comm Type"], "ethernet")
        self.assertEqual(specs["Status"], "Complete")

    def test_formatted_specs_incomplete_status(self):
        """Test formatted_specs shows incomplete status."""
        incomplete_entry = LibraryEntry(
            class_name="TestDevice",
            package="test.module",
            metadata={"name": "Test"},
            is_complete=False,
        )

        specs = incomplete_entry.formatted_specs
        self.assertEqual(specs["Status"], "Incomplete")

    def test_docs_links_returns_dict(self):
        """Test docs_links returns dictionary of URLs."""
        entry = LibraryEntry(
            class_name="WatlowEZZone",
            package="pychron.hardware.watlow.watlow_ezzone",
            metadata={
                "name": "Watlow EZZone PM",
                "description": "Temperature controller",
                "company": "Watlow",
                "model": "PM-100",
                "docs_url": "https://docs.watlow.com",
                "website": "https://watlow.com",
            },
            is_complete=True,
        )
        links = entry.docs_links

        self.assertIsInstance(links, dict)
        self.assertIn("Documentation", links)


class TestLibraryFilter(unittest.TestCase):
    """Tests for Phase 2.2: Advanced filtering."""

    def setUp(self):
        """Set up test fixtures."""
        self.entry1 = LibraryEntry(
            class_name="WatlowEZZone",
            package="pychron.hardware.watlow",
            metadata={
                "name": "Watlow EZZone PM",
                "description": "Temperature controller",
                "company": "Watlow",
                "default_comm_type": "ethernet",
            },
            is_complete=True,
        )

        self.entry2 = LibraryEntry(
            class_name="DummyController",
            package="pychron.hardware.dummy",
            metadata={
                "name": "Dummy Controller",
                "description": "Test device",
                "company": "Test Corp",
                "default_comm_type": "serial",
            },
            is_complete=False,
        )

        self.entry3 = LibraryEntry(
            class_name="AnotherWatlow",
            package="pychron.hardware.watlow",
            metadata={
                "name": "Another Watlow Device",
                "description": "Another controller",
                "company": "Watlow",
                "default_comm_type": "serial",
            },
            is_complete=True,
        )

    def test_filter_no_criteria(self):
        """Test filter with no criteria matches all entries."""
        filter_obj = LibraryFilter()
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 3)

    def test_filter_by_company(self):
        """Test filtering by company name."""
        filter_obj = LibraryFilter(company_filter="Watlow")
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 2)
        self.assertTrue(all(e.company == "Watlow" for e in matches))

    def test_filter_by_comm_type(self):
        """Test filtering by communication type."""
        filter_obj = LibraryFilter(comm_type_filter="ethernet")
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].class_name, "WatlowEZZone")

    def test_filter_by_completeness_complete(self):
        """Test filtering for complete entries only."""
        filter_obj = LibraryFilter(completeness_filter="complete")
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 2)
        self.assertTrue(all(e.is_complete for e in matches))

    def test_filter_by_completeness_incomplete(self):
        """Test filtering for incomplete entries only."""
        filter_obj = LibraryFilter(completeness_filter="incomplete")
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 1)
        self.assertFalse(matches[0].is_complete)

    def test_filter_text_search_name(self):
        """Test full-text search on device name."""
        filter_obj = LibraryFilter(search_text="Watlow")
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 2)

    def test_filter_text_search_description(self):
        """Test full-text search on description."""
        filter_obj = LibraryFilter(search_text="Temperature")
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].class_name, "WatlowEZZone")

    def test_filter_text_search_case_insensitive(self):
        """Test case-insensitive search."""
        filter_obj = LibraryFilter(search_text="watlow")
        matches = [self.entry1, self.entry3]
        self.assertEqual(len([e for e in matches if filter_obj.matches(e)]), 2)

    def test_filter_combined_criteria(self):
        """Test filtering with multiple criteria."""
        filter_obj = LibraryFilter(company_filter="Watlow", comm_type_filter="ethernet")
        entries = [self.entry1, self.entry2, self.entry3]

        matches = [e for e in entries if filter_obj.matches(e)]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].class_name, "WatlowEZZone")

    def test_filter_reset(self):
        """Test reset clears all filters."""
        filter_obj = LibraryFilter(
            search_text="test",
            company_filter="Test",
            comm_type_filter="serial",
            completeness_filter="complete",
        )

        filter_obj.reset()

        self.assertEqual(filter_obj.search_text, "")
        self.assertIsNone(filter_obj.company_filter)
        self.assertIsNone(filter_obj.comm_type_filter)
        self.assertIsNone(filter_obj.completeness_filter)


class TestLibrarySearcher(unittest.TestCase):
    """Tests for Phase 2.2: Search functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.entries = [
            LibraryEntry(
                class_name="WatlowEZZone",
                package="pychron.hardware.watlow",
                metadata={
                    "name": "Watlow EZZone",
                    "description": "Temperature controller",
                    "company": "Watlow",
                    "default_comm_type": "ethernet",
                },
                is_complete=True,
            ),
            LibraryEntry(
                class_name="DummyController",
                package="pychron.hardware.dummy",
                metadata={
                    "name": "Dummy",
                    "description": "Test device",
                    "company": "Test",
                    "default_comm_type": "serial",
                },
                is_complete=False,
            ),
            LibraryEntry(
                class_name="Eurotherm",
                package="pychron.hardware.eurotherm",
                metadata={
                    "name": "Eurotherm 2000",
                    "description": "Temperature controller",
                    "company": "Eurotherm",
                    "default_comm_type": "serial",
                },
                is_complete=True,
            ),
        ]

    def test_get_unique_companies(self):
        """Test getting unique company names."""
        companies = LibrarySearcher.get_unique_companies(self.entries)

        self.assertEqual(len(companies), 3)
        self.assertIn("Watlow", companies)
        self.assertIn("Test", companies)
        self.assertIn("Eurotherm", companies)
        self.assertEqual(companies, sorted(companies))

    def test_get_unique_comm_types(self):
        """Test getting unique communication types."""
        comm_types = LibrarySearcher.get_unique_comm_types(self.entries)

        self.assertEqual(len(comm_types), 2)
        self.assertIn("ethernet", comm_types)
        self.assertIn("serial", comm_types)
        self.assertEqual(comm_types, sorted(comm_types))

    def test_get_completeness_stats(self):
        """Test completeness statistics."""
        total, complete, percentage = LibrarySearcher.get_completeness_stats(self.entries)

        self.assertEqual(total, 3)
        self.assertEqual(complete, 2)
        self.assertAlmostEqual(percentage, 66.67, places=1)

    def test_get_completeness_stats_empty(self):
        """Test completeness stats with empty list."""
        total, complete, percentage = LibrarySearcher.get_completeness_stats([])

        self.assertEqual(total, 0)
        self.assertEqual(complete, 0)
        self.assertEqual(percentage, 0.0)

    def test_search_by_text(self):
        """Test full-text search."""
        results = LibrarySearcher.search_by_text(self.entries, "Watlow")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].class_name, "WatlowEZZone")

    def test_search_by_company(self):
        """Test search by company."""
        results = LibrarySearcher.search_by_company(self.entries, "Watlow")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].company, "Watlow")

    def test_search_by_comm_type(self):
        """Test search by communication type."""
        results = LibrarySearcher.search_by_comm_type(self.entries, "serial")

        self.assertEqual(len(results), 2)
        self.assertTrue(all(e.default_comm_type == "serial" for e in results))

    def test_search_incomplete(self):
        """Test search for incomplete entries."""
        results = LibrarySearcher.search_incomplete(self.entries)

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].is_complete)

    def test_filter_entries(self):
        """Test filter_entries helper."""
        filter_obj = LibraryFilter(company_filter="Watlow")
        results = LibrarySearcher.filter_entries(self.entries, filter_obj)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].company, "Watlow")


class TestMetadataLinks(unittest.TestCase):
    """Tests for Phase 2.1: Interactive metadata links."""

    def test_has_url_with_docs(self):
        """Test has_url returns True when docs_url exists."""
        entry = LibraryEntry(
            class_name="Test",
            package="test",
            metadata={
                "name": "Test",
                "description": "Test",
                "company": "Test",
                "docs_url": "https://example.com",
            },
        )
        self.assertTrue(entry.has_url())

    def test_has_url_with_website(self):
        """Test has_url returns True when website exists."""
        entry = LibraryEntry(
            class_name="Test",
            package="test",
            metadata={
                "name": "Test",
                "description": "Test",
                "company": "Test",
                "website": "https://example.com",
            },
        )
        self.assertTrue(entry.has_url())

    def test_has_url_with_both(self):
        """Test has_url returns True when both URLs exist."""
        entry = LibraryEntry(
            class_name="Test",
            package="test",
            metadata={
                "name": "Test",
                "description": "Test",
                "company": "Test",
                "docs_url": "https://docs.example.com",
                "website": "https://example.com",
            },
        )
        self.assertTrue(entry.has_url())

    def test_has_url_without_urls(self):
        """Test has_url returns False when no URLs exist."""
        entry = LibraryEntry(
            class_name="Test",
            package="test",
            metadata={
                "name": "Test",
                "description": "Test",
                "company": "Test",
            },
        )
        self.assertFalse(entry.has_url())

    def test_docs_links_dict(self):
        """Test docs_links returns correct dictionary."""
        entry = LibraryEntry(
            class_name="Test",
            package="test",
            metadata={
                "name": "Test",
                "description": "Test",
                "company": "Test",
                "docs_url": "https://docs.example.com",
                "website": "https://example.com",
                "manual": "https://manual.example.com",
            },
        )
        links = entry.docs_links

        self.assertEqual(len(links), 3)
        self.assertEqual(links["Documentation"], "https://docs.example.com")
        self.assertEqual(links["Manufacturer"], "https://example.com")
        self.assertEqual(links["Manual"], "https://manual.example.com")


if __name__ == "__main__":
    unittest.main()

# ============= EOF =============================================
