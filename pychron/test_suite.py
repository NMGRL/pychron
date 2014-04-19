__author__ = 'ross'
import unittest

from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest, FilterOLSRegressionTest
from pychron.processing.tests.plateau import PlateauTestCase
from pychron.external_pipette.tests.external_pipette import ExternalPipetteTestCase


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # suite.addTest(loader.loadTestsFromTestCase(RegressionTestCase))
    suite.addTest(loader.loadTestsFromTestCase(OLSRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(MeanRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(FilterOLSRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(PlateauTestCase))
    suite.addTest(loader.loadTestsFromTestCase(ExternalPipetteTestCase))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

