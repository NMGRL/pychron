__author__ = 'ross'
import unittest

from pychron.processing.plateau import Plateau


class MyTestCase(unittest.TestCase):
    # def test_find_plateaus_real_fail(self):
    #     ages, errors, signals, idx = self._get_test_data_real_fail()
    #     p = Plateau(ages=ages, errors=errors, signals=signals)
    #     pidx = p.find_plateaus()
    #
    #     self.assertEqual(pidx, idx)
    #
    # def _get_test_data_real_fail(self):
    #     from numpy import array
    #     ages=array((35.868552979882665, 28.65120030078213, 42.50497290609334, 7.07438966261561, 4.195660871265764,
    #      1.0858792249353095, -0.4221166626917233, -0.12004830840675619, 1.8853011443998902, 1.5780258768875648,
    #      -10.101645211071741))
    #     errors=array((6.919989216306931, 7.049527127933513, 9.145756003423196, 6.686552442442291, 0.8886617073346395,
    #      0.7169908023518705, 0.8929036679198642, 0.8519646228626566, 0.731753931175695, 0.5282504703465821,
    #      0.6748271815689348))
    #     signals=array((0.7810246769509941, 0.8740964805271505, 0.6292251586876362, 0.7018528668884262, 17.38003337391667,
    #      27.8410907332066, 20.16578297006377, 21.992348007909765, 27.11825018093817, 54.38147532790856,
    #      52.794784404872196))
    #     idx = []
    #     return ages, errors, signals, idx


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
