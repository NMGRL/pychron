
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
    from pychron.experiment.tests.conditionals import ConditionalsTestCase
    from pychron.experiment.tests.identifier import IdentifierTestCase
    from pychron.experiment.tests.comment_template import CommentTemplaterTestCase

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tests = (XLSAnalysisLoaderTestCase,
             RatioTestCase,
             InterpolationTestCase,
             DocstrContextTestCase,
             OLSRegressionTest,
             MeanRegressionTest,
             FilterOLSRegressionTest,
             PlateauTestCase,
             ExternalPipetteTestCase,
             WaitForTestCase,
             XYTestCase,
             FrequencyTestCase,
             RenumberAliquotTestCase,
             ConditionalsTestCase,
             IdentifierTestCase,
             CommentTemplaterTestCase)
    for t in tests:
        suite.addTest(loader.loadTestsFromTestCase(t))

    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

