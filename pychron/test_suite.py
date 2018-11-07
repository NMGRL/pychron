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

    # Canvas
    from pychron.canvas.canvas2D.tests.calibration_item import CalibrationObjectTestCase

    # Core
    from pychron.core.tests.spell_correct import SpellCorrectTestCase
    from pychron.core.tests.filtering_tests import FilteringTestCase
    from pychron.core.stats.tests.peak_detection_test import MultiPeakDetectionTestCase
    from pychron.core.helpers.tests.floatfmt import FloatfmtTestCase
    from pychron.core.helpers.tests.strtools import CamelCaseTestCase
    from pychron.core.xml.tests.xml_parser import XMLParserTestCase
    from pychron.core.regression.tests.regression import OLSRegressionTest, MeanRegressionTest, \
        FilterOLSRegressionTest, OLSRegressionTest2, TruncateRegressionTest, ExpoRegressionTest, ExpoRegressionTest2

    # DataMapper
    from pychron.data_mapper.tests.usgs_vsc_file_source import USGSVSCFileSourceUnittest, \
        USGSVSCIrradiationSourceUnittest
    from pychron.data_mapper.tests.nu_file_source import NuFileSourceUnittest
    from pychron.data_mapper.tests.nmgrl_legacy_source import NMGRLLegacySourceUnittest

    # Experiment
    from pychron.experiment.tests.repository_identifier import ExperimentIdentifierTestCase
    from pychron.experiment.tests.peak_hop_parse import PeakHopYamlCase1
    from pychron.experiment.tests.peak_hop_parse import PeakHopYamlCase2
    from pychron.experiment.tests.backup import BackupTestCase
    from pychron.experiment.tests.peak_hop_parse import PeakHopTxtCase
    from pychron.experiment.tests.duration_tracker import DurationTrackerTestCase
    from pychron.experiment.tests.frequency_test import FrequencyTestCase, FrequencyTemplateTestCase
    from pychron.experiment.tests.position_regex_test import XYTestCase
    from pychron.experiment.tests.renumber_aliquot_test import RenumberAliquotTestCase
    from pychron.experiment.tests.conditionals import ConditionalsTestCase, ParseConditionalsTestCase
    from pychron.experiment.tests.identifier import IdentifierTestCase
    from pychron.experiment.tests.comment_template import CommentTemplaterTestCase

    # ExternalPipette
    from pychron.external_pipette.tests.external_pipette import ExternalPipetteTestCase

    # Processing
    from pychron.processing.tests.plateau import PlateauTestCase
    from pychron.processing.tests.ratio import RatioTestCase
    from pychron.processing.tests.age_converter import AgeConverterTestCase

    # Pyscripts
    from pychron.pyscripts.tests.extraction_script import WaitForTestCase
    from pychron.pyscripts.tests.measurement_pyscript import InterpolationTestCase, DocstrContextTestCase

    # Spectrometer
    from pychron.spectrometer.tests.mftable import MFTableTestCase, DiscreteMFTableTestCase
    from pychron.spectrometer.tests.integration_time import IntegrationTimeTestCase

    from pychron.stage.tests.stage_map import StageMapTestCase, TransformTestCase

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tests = (
        # Canvas
        CalibrationObjectTestCase,

        # Core
        SpellCorrectTestCase,
        FilteringTestCase,
        MultiPeakDetectionTestCase,
        FloatfmtTestCase,
        CamelCaseTestCase,
        RatioTestCase,
        XMLParserTestCase,
        OLSRegressionTest,
        MeanRegressionTest,
        ExpoRegressionTest,
        ExpoRegressionTest2,
        FilterOLSRegressionTest,
        OLSRegressionTest2,
        TruncateRegressionTest,

        # DataMapper
        USGSVSCFileSourceUnittest,
        USGSVSCIrradiationSourceUnittest,
        NuFileSourceUnittest,
        NMGRLLegacySourceUnittest,

        # Experiment
        ExperimentIdentifierTestCase,
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
        WaitForTestCase,
        InterpolationTestCase,
        DocstrContextTestCase,

        # Spectrometer
        MFTableTestCase,
        DiscreteMFTableTestCase,
        IntegrationTimeTestCase,

        # Stage
        StageMapTestCase, TransformTestCase)

    for t in tests:
        suite.addTest(loader.loadTestsFromTestCase(t))

    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
