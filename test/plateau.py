__author__ = 'ross'
import unittest

from pychron.processing.plateau import Plateau


class MyTestCase(unittest.TestCase):
    def test_find_plateaus_pass1(self):
        ages, errors, signals, idx = self._get_test_data_pass1()
        p = Plateau(ages=ages, errors=errors, signals=signals)
        pidx = p.find_plateaus()

        self.assertEqual(pidx, idx)

    def _get_test_data_pass1(self):
        ages = [1, 1, 1, 1, 1, 6, 7]
        errors = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        signals = [1, 1, 1, 1, 1, 1, 1]

        idx = (0, 4)
        return ages, errors, signals, idx

    def test_find_plateaus_pass2(self):
        ages, errors, signals, idx = self._get_test_data_pass2()
        p = Plateau(ages=ages, errors=errors, signals=signals)
        pidx = p.find_plateaus()

        self.assertEqual(pidx, idx)

    def _get_test_data_pass2(self):
        ages = [7, 1, 1, 1, 1, 6, 7]
        errors = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        signals = [1, 1, 1, 1, 1, 1, 1]

        idx = (1, 4)
        return ages, errors, signals, idx

    def test_find_plateaus_fail1(self):
        ages, errors, signals, idx = self._get_test_data_fail1()
        p = Plateau(ages=ages, errors=errors, signals=signals)
        pidx = p.find_plateaus()

        self.assertEqual(pidx, idx)

    def _get_test_data_fail1(self):
        ages = [7, 1, 1, 1, 1, 6, 7]
        errors = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        signals = [1, 1, 1, 1, 1, 1, 100]

        idx = []
        return ages, errors, signals, idx

    def test_find_plateaus_exclude_pass(self):
        ages, errors, signals, exclude, idx = self._get_test_data_exclude_pass()
        p = Plateau(ages=ages, errors=errors,
                    exclude=exclude,
                    signals=signals)
        pidx = p.find_plateaus()

        self.assertEqual(pidx, idx)

    def _get_test_data_exclude_pass(self):
        ages = [7, 1, 1, 1, 1, 6, 7]
        errors = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        signals = [1, 1, 1, 1, 1, 1, 100]
        exclude = [6]
        idx = (1, 4)
        return ages, errors, signals, exclude, idx


if __name__ == '__main__':
    unittest.main()
