from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest

__author__ = 'ross'
import unittest


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(OLSRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(MeanRegressionTest))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
