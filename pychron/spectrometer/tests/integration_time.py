import unittest

from pychron.spectrometer.thermo.spectrometer.base import normalize_integration_time


class IntegrationTimeTestCase(unittest.TestCase):
    def test_normalize(self):
        itin = [0.066, 0.06,
                0.13, 0.1,
                0.26, 0.2,
                0.52, 0.5,
                1, 2, 4, 8, 16, 33, 67]

        expected = [0.065536,
                    0.065536,
                    0.131072,
                    0.131072,
                    0.262144,
                    0.262144,
                    0.524288,
                    0.524288,
                    1.048576, 2.097152, 4.194304, 8.388608,
                    16.777216, 33.554432, 67.108864]
        out = []
        for i in itin:
            o = normalize_integration_time(i)
            out.append(o)

        self.assertListEqual(out, expected)


if __name__ == '__main__':
    unittest.main()
