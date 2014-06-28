__author__ = 'ross'
import unittest



def suite():
    from pychron.entry.tests.analysis_loader import XLSAnalysisLoaderTestCase

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(loader.loadTestsFromTestCase(XLSAnalysisLoaderTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(RatioTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(InterpolationTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(DocstrContextTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(OLSRegressionTest))
    # suite.addTest(loader.loadTestsFromTestCase(MeanRegressionTest))
    # suite.addTest(loader.loadTestsFromTestCase(FilterOLSRegressionTest))
    # suite.addTest(loader.loadTestsFromTestCase(PlateauTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(ExternalPipetteTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(WaitForTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(XYTestCase))
    # suite.addTest(loader.loadTestsFromTestCase(FrequencyTestCase))


    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

