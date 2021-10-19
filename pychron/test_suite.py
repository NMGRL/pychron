import os
import unittest

from pychron.canvas.canvas2D.tests.calibration_item import CalibrationObjectTestCase
from pychron.core.helpers.tests.floatfmt import SigFigStdFmtTestCase
from pychron.core.stats.tests.mswd_tests import MSWDTestCase

# from pychron.pyscripts.tests.extraction_script import WaitForTestCase
# from pychron.canvas.canvas2D.tests.calibration_item import CalibrationObjectTestCase
#
# # Core
from pychron.core.stats.tests.peak_detection_test import MultiPeakDetectionTestCase
from pychron.core.tests.spell_correct import SpellCorrectTestCase
from pychron.core.tests.filtering_tests import FilteringTestCase

# from pychron.core.stats.tests.peak_detection_test import MultiPeakDetectionTestCase
from pychron.core.helpers.tests.floatfmt import FloatfmtTestCase
from pychron.core.helpers.tests.strtools import CamelCaseTestCase

from pychron.core.xml.tests.xml_parser import XMLParserTestCase
from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest, \
    FilterOLSRegressionTest, OLSRegressionTest2, TruncateRegressionTest
from pychron.core.tests.alpha_tests import AlphaTestCase
from pychron.experiment.tests.backup import BackupTestCase
from pychron.experiment.tests.comment_template import CommentTemplaterTestCase
from pychron.experiment.tests.conditionals import ConditionalsTestCase, ParseConditionalsTestCase
from pychron.experiment.tests.duration_tracker import DurationTrackerTestCase
from pychron.experiment.tests.frequency_test import FrequencyTestCase, FrequencyTemplateTestCase
from pychron.experiment.tests.identifier import IdentifierTestCase
from pychron.experiment.tests.peak_hop_parse import PeakHopYamlCase1, PeakHopTxtCase
from pychron.experiment.tests.peak_hop_parse import PeakHopYamlCase2
from pychron.experiment.tests.position_regex_test import XYTestCase
from pychron.experiment.tests.renumber_aliquot_test import RenumberAliquotTestCase
from pychron.external_pipette.tests.external_pipette import ExternalPipetteTestCase
from pychron.processing.tests.age_converter import AgeConverterTestCase
from pychron.processing.tests.plateau import PlateauTestCase
from pychron.processing.tests.ratio import RatioTestCase
from pychron.spectrometer.tests.integration_time import IntegrationTimeTestCase
from pychron.spectrometer.tests.mftable import DiscreteMFTableTestCase
from pychron.stage.tests.stage_map import StageMapTestCase, TransformTestCase
#
# os.environ['MassSpecDBVersion'] = '16'
#
# from pychron.paths import paths
#
# paths.build('_dev')
#
# use_logger = False
#
#
def suite():
    # set env. variables
    os.environ["MassSpecDBVersion"] = "16"

    from pychron.paths import paths

    paths.build("_dev")

    # if use_logger:
    #     from pychron.core.helpers.logger_setup import logging_setup
    #     logging_setup('unittests')

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tests = (
        # Canvas
        CalibrationObjectTestCase,
        # Core
        AlphaTestCase,
        SpellCorrectTestCase,
        FilteringTestCase,
        MultiPeakDetectionTestCase,
        FloatfmtTestCase,
        SigFigStdFmtTestCase,
        CamelCaseTestCase,
        RatioTestCase,
        XMLParserTestCase,
        OLSRegressionTest,
        MeanRegressionTest,
        FilterOLSRegressionTest,
        OLSRegressionTest2,
        TruncateRegressionTest,
        MSWDTestCase,
        # old
        # ExpoRegressionTest,
        # ExpoRegressionTest2,

        # DataMapper
        # USGSVSCFileSourceUnittest,
        # USGSVSCIrradiationSourceUnittest,
        # NMGRLLegacySourceUnittest,

        # Experiment
        PeakHopYamlCase1,
        PeakHopYamlCase2,
        BackupTestCase,
        PeakHopTxtCase,
        DurationTrackerTestCase,
        FrequencyTestCase,
        FrequencyTemplateTestCase,
        XYTestCase,
        RenumberAliquotTestCase,
        ConditionalsTestCase,
        ParseConditionalsTestCase,
        IdentifierTestCase,
        CommentTemplaterTestCase,
        # ExternalPipette
        ExternalPipetteTestCase,
        # Processing
        PlateauTestCase,
        RatioTestCase,
        AgeConverterTestCase,
        # Pyscripts
        # WaitForTestCase,
        # InterpolationTestCase,
        # DocstrContextTestCase,
        # Spectrometer
        # MFTableTestCase,
        DiscreteMFTableTestCase,
        IntegrationTimeTestCase,

        # Stage
        StageMapTestCase,
        TransformTestCase
    )

    for t in tests:
        suite.addTest(loader.loadTestsFromTestCase(t))

    return suite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
