__author__ = 'ross'
import unittest

from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest, FilterOLSRegressionTest


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # suite.addTest(loader.loadTestsFromTestCase(RegressionTestCase))
    suite.addTest(loader.loadTestsFromTestCase(OLSRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(MeanRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(FilterOLSRegressionTest))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

