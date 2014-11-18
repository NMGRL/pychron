__author__ = 'ross'
import unittest

from pychron.processing.plateau import Plateau


class PlateauTestCase(unittest.TestCase):
    def test_find_plateaus_real_fail(self):
        ages, errors, signals, idx = self._get_test_data_real_fail()
        p = Plateau(ages=ages, errors=errors, signals=signals)
        pidx = p.find_plateaus()

        self.assertEqual(pidx, idx)

    #
    def _get_test_data_real_fail(self):
        from numpy import array
        # ages=array((35.868552979882665, 28.65120030078213, 42.50497290609334, 7.07438966261561, 4.195660871265764,
        #  1.0858792249353095, -0.4221166626917233, -0.12004830840675619, 1.8853011443998902, 1.5780258768875648,
        #  -10.101645211071741))
        # errors=array((6.919989216306931, 7.049527127933513, 9.145756003423196, 6.686552442442291, 0.8886617073346395,
        #  0.7169908023518705, 0.8929036679198642, 0.8519646228626566, 0.731753931175695, 0.5282504703465821,
        #  0.6748271815689348))
        # signals=array((0.7810246769509941, 0.8740964805271505, 0.6292251586876362, 0.7018528668884262, 17.38003337391667,
        #  27.8410907332066, 20.16578297006377, 21.992348007909765, 27.11825018093817, 54.38147532790856,
        #  52.794784404872196))
        # idx = []
        # ages = array((-4.532789592132701, 3.0251903778384652, 12.984282904655316, 7.415675559405696, 9.915514634333844,
        #               5.073849627600819, 11.366067628509356, 9.84552044626644, 8.666915528926422, 5.651212206628916))
        # errors = array(
        #     (9.675981872958216, 2.040698750519321, 1.2507687776259215, 1.6834363119706215, 1.6428286793048248,
        #      2.34821762863906, 2.261712182530417, 1.3828420070106184, 0.8055989308667363, 12.159308987062149))
        # signals = (
        # (0.008781579340722387, 0.022572166331206355, 0.02555511093162022, 0.01598356585916768, 0.017556082863965577,
        #  0.018822676982304394, 0.017648844197362533, 0.013847882976741893, 0.07265460797899809, 0.00247174971560797))
        # idx = (3, 9)
        ages = array((
            0.0, -1.7876025629846548, 6.032764579857944, 2.7397332580523464, 4.460694361094021, 10.315258068397155,
            1.9608161615417614, 4.243254226544221, 2.351015213399544, 20.30464547047681, 35.661743844775906,
            2.6230194593952936))
        errors = array((
            0.0, 2.512262658455881, 1.1274599800062448, 1.4118647248494784, 1.6742580841211745, 1.2757804416214515,
            1.0106219474747273, 1.0445217309056742, 1.7340042145883465, 1.5479507323926824, 3.1237570168227484,
            4.443268510171474))
        k39 = array((
            4.589247099994707e-06, 0.03635680262539634, 0.0470548608081756, 0.03438849848233932, 0.03450855667611368,
            0.049794029194755805, 0.03710497981315457, 0.019496051872155938, 0.02132742877176139, 0.11441612176437539,
            0.020311606200646422, 0.004718409859914923))

        idx = []
        return ages, errors, k39, idx


    def test_find_plateaus_pass1(self):
        ages, errors, signals, idx = self._get_test_data_pass1()
        p = Plateau(ages=ages, errors=errors, signals=signals)
        pidx = p.find_plateaus()

        self.assertEqual(pidx, idx)

    def _get_test_data_pass1(self):
        # ages = [1, 1, 1, 1, 1, 6, 7]
        ages = [1, 1, 1, 1, 1, 1, 1]
        errors = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        signals = [1, 1, 1, 1, 1, 1, 1]

        idx = (0, 6)
        return ages, errors, signals, idx

    #
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
