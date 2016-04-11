
__author__ = 'ross'

import os
import unittest

use_logger = False


def suite():
    # set env. variables
    os.environ['MassSpecDBVersion'] = '16'

    from pychron.paths import paths
    paths.build('_dev')

    if use_logger:
        from pychron.core.helpers.logger_setup import logging_setup
        logging_setup('unittests')

    from pychron.canvas.canvas2D.tests.calibration_item import CalibrationObjectTestCase
    from pychron.experiment.tests.duration_tracker import DurationTrackerTestCase
    from pychron.core.tests.spell_correct import SpellCorrectTestCase
    from pychron.entry.tests.irradiation_loader import SimilarTestCase
    from pychron.core.tests.filtering_tests import FilteringTestCase
    from pychron.core.stats.tests.peak_detection_test import MultiPeakDetectionTestCase
    from pychron.experiment.tests.repository_identifier import ExperimentIdentifierTestCase

    from pychron.stage.tests.stage_map import StageMapTestCase, \
        TransformTestCase
    from pychron.entry.tests.sample_loader import SampleLoaderTestCase
    from pychron.core.helpers.tests.floatfmt import FloatfmtTestCase
    from pychron.processing.tests.analysis_modifier import AnalysisModifierTestCase
    from pychron.experiment.tests.backup import BackupTestCase
    from pychron.core.xml.tests.xml_parser import XMLParserTestCase
    from pychron.entry.tests.analysis_loader import XLSAnalysisLoaderTestCase
    from pychron.entry.tests.irradiation_loader import XLSIrradiationLoaderParseTestCase, \
        XLSIrradiationLoaderLoadTestCase
    # from pychron.entry.tests.massspec_irrad_export import MassSpecIrradExportTestCase
    from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest, \
        FilterOLSRegressionTest, OLSRegressionTest2
    from pychron.experiment.tests.frequency_test import FrequencyTestCase, FrequencyTemplateTestCase
    from pychron.experiment.tests.position_regex_test import XYTestCase
    from pychron.experiment.tests.renumber_aliquot_test import RenumberAliquotTestCase

    from pychron.external_pipette.tests.external_pipette import ExternalPipetteTestCase
    from pychron.processing.tests.plateau import PlateauTestCase
    from pychron.processing.tests.ratio import RatioTestCase
    from pychron.pyscripts.tests.extraction_script import WaitForTestCase
    from pychron.pyscripts.tests.measurement_pyscript import InterpolationTestCase, DocstrContextTestCase
    from pychron.experiment.tests.conditionals import ConditionalsTestCase, ParseConditionalsTestCase
    from pychron.experiment.tests.identifier import IdentifierTestCase
    from pychron.experiment.tests.comment_template import CommentTemplaterTestCase

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tests = (CalibrationObjectTestCase,
             DurationTrackerTestCase,
             SpellCorrectTestCase,
             SimilarTestCase,
             FilteringTestCase,
             MultiPeakDetectionTestCase,
             ExperimentIdentifierTestCase,
             StageMapTestCase,
             TransformTestCase,
             SampleLoaderTestCase,
             AnalysisModifierTestCase,
             BackupTestCase,
             # MassSpecIrradExportTestCase,
             XMLParserTestCase,
             XLSIrradiationLoaderLoadTestCase,
             XLSIrradiationLoaderParseTestCase,
             XLSAnalysisLoaderTestCase,

             RatioTestCase,
             InterpolationTestCase,
             DocstrContextTestCase,
             OLSRegressionTest,
             OLSRegressionTest2,
             MeanRegressionTest,
             FilterOLSRegressionTest,
             PlateauTestCase,
             ExternalPipetteTestCase,
             WaitForTestCase,
             XYTestCase,
             FrequencyTestCase,
             FrequencyTemplateTestCase,
             RenumberAliquotTestCase,
             ConditionalsTestCase,
             ParseConditionalsTestCase,
             IdentifierTestCase,
             CommentTemplaterTestCase,
             FloatfmtTestCase)

    for t in tests:
        suite.addTest(loader.loadTestsFromTestCase(t))

    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

