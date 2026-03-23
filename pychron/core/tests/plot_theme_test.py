import unittest

from pychron.graph.theme import themed_container_dict, themed_plot_bgcolor


class PlotThemeTestCase(unittest.TestCase):
    def test_themed_container_dict_defaults(self):
        options = themed_container_dict()
        self.assertEqual(options["bgcolor"], "white")
        self.assertEqual(options["padding"], 5)
        self.assertTrue(options["fill_padding"])

    def test_themed_plot_bgcolor_normalizes(self):
        self.assertEqual(themed_plot_bgcolor("light grey"), "lightgray")


if __name__ == "__main__":
    unittest.main()
