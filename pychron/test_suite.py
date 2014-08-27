__author__ = 'ross'
import unittest


def suite():
    from pychron.entry.tests.analysis_loader import XLSAnalysisLoaderTestCase
    from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest, FilterOLSRegressionTest
    from pychron.experiment.tests.frequency_test import FrequencyTestCase
    from pychron.experiment.tests.position_regex_test import XYTestCase
    from pychron.experiment.tests.renumber_aliquot_test import RenumberAliquotTestCase

    from pychron.external_pipette.tests.external_pipette import ExternalPipetteTestCase
    from pychron.processing.tests.plateau import PlateauTestCase
    from pychron.processing.tests.ratio import RatioTestCase
    from pychron.pyscripts.tests.extraction_script import WaitForTestCase
    from pychron.pyscripts.tests.measurement_pyscript import InterpolationTestCase, DocstrContextTestCase

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(loader.loadTestsFromTestCase(XLSAnalysisLoaderTestCase))
    suite.addTest(loader.loadTestsFromTestCase(RatioTestCase))
    suite.addTest(loader.loadTestsFromTestCase(InterpolationTestCase))
    suite.addTest(loader.loadTestsFromTestCase(DocstrContextTestCase))
    suite.addTest(loader.loadTestsFromTestCase(OLSRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(MeanRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(FilterOLSRegressionTest))
    suite.addTest(loader.loadTestsFromTestCase(PlateauTestCase))
    suite.addTest(loader.loadTestsFromTestCase(ExternalPipetteTestCase))
    suite.addTest(loader.loadTestsFromTestCase(WaitForTestCase))
    suite.addTest(loader.loadTestsFromTestCase(XYTestCase))
    suite.addTest(loader.loadTestsFromTestCase(FrequencyTestCase))
    suite.addTest(loader.loadTestsFromTestCase(RenumberAliquotTestCase))

    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

