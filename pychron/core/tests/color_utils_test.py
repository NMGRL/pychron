import unittest

from pychron.core.helpers.color_utils import (
    coerce_qcolor,
    contrast_color,
    normalize_color_name,
    to_hex,
    to_rgba255,
    to_rgba_float,
)


class DummyQColor:
    def __init__(self, *args):
        self.args = args


class DummyColor:
    def __init__(self, rgba):
        self.rgba = rgba


class ColorUtilsTestCase(unittest.TestCase):
    def test_normalize_color_name_aliases(self):
        self.assertEqual(normalize_color_name("light grey"), "lightgray")
        self.assertEqual(normalize_color_name("blue violet"), "blueviolet")
        self.assertEqual(normalize_color_name("transparent"), "clear")

    def test_to_rgba255_from_named_color(self):
        self.assertEqual(to_rgba255("green"), (0, 127, 0, 255))

    def test_to_rgba255_from_float_tuple(self):
        self.assertEqual(to_rgba255((1.0, 0.5, 0.0, 0.5)), (255, 128, 0, 128))

    def test_to_rgba255_from_object_rgba_sequence(self):
        self.assertEqual(to_rgba255(DummyColor((0.0, 0.0, 1.0, 1.0))), (0, 0, 255, 255))

    def test_to_rgba_float_from_named_color(self):
        self.assertEqual(to_rgba_float("black"), (0.0, 0.0, 0.0, 1.0))

    def test_to_hex(self):
        self.assertEqual(to_hex((255, 0, 0)), "#ff0000")
        self.assertEqual(to_hex((255, 0, 0, 128), include_alpha=True), "#ff000080")

    def test_contrast_color(self):
        self.assertEqual(contrast_color("white"), "black")
        self.assertEqual(contrast_color("navy"), "white")

    def test_coerce_qcolor_uses_normalized_color(self):
        color = coerce_qcolor("light grey", qcolor_class=DummyQColor)
        self.assertEqual(color.args, ("lightgray",))

    def test_coerce_qcolor_uses_rgba_components(self):
        color = coerce_qcolor((255, 0, 0, 128), qcolor_class=DummyQColor)
        self.assertEqual(color.args, (255, 0, 0, 128))


if __name__ == "__main__":
    unittest.main()
