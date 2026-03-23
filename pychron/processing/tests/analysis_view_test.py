import unittest

from pychron.processing.analyses.view.main_view import MainView
from pychron.processing.analyses.view.values import MeasurementValue
from pychron.processing.isotope import Isotope


class MainViewValueReuseTestCase(unittest.TestCase):
    def test_sync_values_reuses_existing_items_when_shape_matches(self):
        mv = MainView()
        existing = [MeasurementValue(name="A", value="1")]
        new_values = [MeasurementValue(name="A", value="2")]

        result = mv._sync_values(existing, new_values, "_measurement_names")

        self.assertIs(result, existing)
        self.assertEqual(existing[0].value, "2")

    def test_sync_values_replaces_items_when_names_change(self):
        mv = MainView()
        existing = [MeasurementValue(name="A", value="1")]
        new_values = [MeasurementValue(name="B", value="2")]

        result = mv._sync_values(existing, new_values, "_measurement_names")

        self.assertIs(result, new_values)


class IsotopeInvalidationTestCase(unittest.TestCase):
    def test_set_grouping_same_value_preserves_regressor(self):
        iso = Isotope("Ar40", "H1")
        reg = object()
        iso._regressor = reg
        iso.group_data = 3

        iso.set_grouping(3)

        self.assertIs(iso._regressor, reg)

    def test_set_grouping_new_value_invalidates_regressor(self):
        iso = Isotope("Ar40", "H1")
        reg = object()
        iso._regressor = reg

        iso.set_grouping(2)

        self.assertIsNone(iso._regressor)


if __name__ == "__main__":
    unittest.main()
