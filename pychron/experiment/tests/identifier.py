from pychron.experiment.utilities.identifier import get_analysis_type

__author__ = 'argonlab2'

import unittest


class IdentifierTestCase(unittest.TestCase):
    def test_background(self):
        self._atype_tester('bg-01-J', 'background')

    def test_blank_air(self):
        self._atype_tester('ba-01-J', 'blank_air')

    def test_blank_unknown(self):
        self._atype_tester('bu-01-J', 'blank_unknown')

    def test_blank_cocktail(self):
        self._atype_tester('bc-01-J', 'blank_cocktail')

    def test_air(self):
        self._atype_tester('a-01-J', 'air')

    def test_cocktail(self):
        self._atype_tester('c-01-J', 'cocktail')

    def test_unknown(self):
        self._atype_tester('12345-01', 'unknown')

    def test_degas(self):
        self._atype_tester('dg', 'degas')

    def test_pause(self):
        self._atype_tester('pa', 'pause')

    def test_detector_ic(self):
        self._atype_tester('ic-01-j', 'detector_ic')

    def _atype_tester(self, idn, atype):
        self.assertEqual(get_analysis_type(idn), atype)


if __name__ == '__main__':
    unittest.main()
