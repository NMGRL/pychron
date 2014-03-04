# from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest, FilterOLSRegressionTest
from pychron.core.regression.tests.regression import MeanRegressionTest
# from pychron.core.regression.tests.regression import RegressionTestCase

__author__ = 'ross'
import unittest


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # suite.addTest(loader.loadTestsFromTestCase(RegressionTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(OLSRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(MeanRegressionTest))
    # suite.addTest(loader.loadTestsFromTestCase(FilterOLSRegressionTest))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
