import os
import unittest

from pychron.canvas.canvas2D.tests.calibration_item import CalibrationObjectTestCase
from pychron.core.helpers.tests.floatfmt import FloatfmtTestCase
from pychron.core.helpers.tests.floatfmt import SigFigStdFmtTestCase
from pychron.core.helpers.tests.strtools import CamelCaseTestCase
from pychron.core.regression.tests.regression import (
    OLSRegressionTest,
    MeanRegressionTest,
    FilterOLSRegressionTest,
    OLSRegressionTest2,
    RegressorStateTrackingTest,
    TruncateRegressionTest,
    NewYorkRegressionTest,
    # ReedRegressionTest,
    PearsonRegressionTest,
)
from pychron.core.stats.tests.mswd_tests import MSWDTestCase
# # Core
from pychron.core.stats.tests.peak_detection_test import MultiPeakDetectionTestCase
from pychron.core.tests.alpha_tests import AlphaTestCase
from pychron.core.tests.bootstrap_profiles_test import BootstrapProfilesTestCase
from pychron.core.tests.color_utils_test import ColorUtilsTestCase
from pychron.core.tests.device_bootstrap_test import DeviceBootstrapTestCase
from pychron.core.tests.filtering_tests import FilteringTestCase
from pychron.core.tests.github_auth_test import GitHubAuthTestCase
from pychron.core.tests.install_bootstrap_test import InstallBootstrapTestCase
from pychron.core.tests.install_support_test import InstallSupportTestCase
from pychron.core.tests.install_validation_test import InstallValidationTestCase
from pychron.core.tests.plot_theme_test import PlotThemeTestCase
from pychron.core.tests.spell_correct import SpellCorrectTestCase
from pychron.core.tests.starter_bundles_test import StarterBundlesTestCase
from pychron.core.xml.tests.xml_parser import XMLParserTestCase
from pychron.dvc.tests.test_data_collection_sync import DataCollectionSyncTestCase
from pychron.experiment.tests.backup import BackupTestCase
from pychron.experiment.tests.comment_template import CommentTemplaterTestCase
from pychron.experiment.tests.conditionals import (
    ConditionalsTestCase,
    ParseConditionalsTestCase,
)
from pychron.experiment.tests.conditionals_actions import (
    ConditionalQueueActionTestCase,
)
from pychron.experiment.tests.conditionals_configuration import (
    ConditionalConfigurationTestCase,
)
from pychron.experiment.tests.duration_tracker import DurationTrackerTestCase
from pychron.experiment.tests.editor_executor_sync import ExperimentExecutorSyncTestCase
from pychron.experiment.tests.editor_performance import ExperimentEditorPerformanceTestCase
from pychron.experiment.tests.frequency_test import (
    FrequencyTestCase,
    FrequencyTemplateTestCase,
)
from pychron.experiment.tests.identifier import IdentifierTestCase
from pychron.experiment.tests.peak_hop_parse import PeakHopYamlCase1, PeakHopTxtCase
from pychron.experiment.tests.peak_hop_parse import PeakHopYamlCase2
from pychron.experiment.tests.position_regex_test import XYTestCase
from pychron.experiment.tests.pyscript_integration import PyScriptIntegrationTestCase
from pychron.experiment.tests.queue_metadata import QueueMetadataPropagationTestCase
from pychron.experiment.tests.renumber_aliquot_test import RenumberAliquotTestCase
from pychron.experiment.tests.repository_identifier import ExperimentIdentifierTestCase
from pychron.experiment.tests.state_machine import AutomatedRunStateMachineTestCase
from pychron.experiment.tests.stats_responsiveness import StatsResponsivenessTestCase
from pychron.external_pipette.tests.external_pipette import ExternalPipetteTestCase
from pychron.pipeline.tests.figure_model_test import FigureModelRefreshTestCase
from pychron.pipeline.tests.figure_panel_limits_test import FigurePanelLimitTestCase
from pychron.pipeline.tests.grid_axis_visibility_test import GridAxisVisibilityTestCase
from pychron.processing.tests.age_converter import AgeConverterTestCase
from pychron.processing.tests.analysis_view_test import (
    MainViewValueReuseTestCase,
    IsotopeInvalidationTestCase,
)
from pychron.processing.tests.plateau import PlateauTestCase
from pychron.processing.tests.ratio import RatioTestCase
from pychron.pyscripts.tests.pyscript_runtime import PyScriptRuntimeTestCase
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
from pychron.spectrometer.tests.integration_time import IntegrationTimeTestCase
from pychron.spectrometer.tests.mftable import DiscreteMFTableTestCase
from pychron.spectrometer.tests.ngx_acquisition_test import NGXAcquisitionTestCase
from pychron.stage.tests.stage_map import StageMapTestCase, TransformTestCase


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
        BootstrapProfilesTestCase,
        ColorUtilsTestCase,
        DeviceBootstrapTestCase,
        GitHubAuthTestCase,
        InstallBootstrapTestCase,
        StarterBundlesTestCase,
        InstallValidationTestCase,
        InstallSupportTestCase,
        PlotThemeTestCase,
        MultiPeakDetectionTestCase,
        FloatfmtTestCase,
        SigFigStdFmtTestCase,
        CamelCaseTestCase,
        RatioTestCase,
        FigurePanelLimitTestCase,
        FigureModelRefreshTestCase,
        GridAxisVisibilityTestCase,
        FigurePanelLimitTestCase,
        FigureModelRefreshTestCase,
        XMLParserTestCase,
        OLSRegressionTest,
        MeanRegressionTest,
        FilterOLSRegressionTest,
        OLSRegressionTest2,
        RegressorStateTrackingTest,
        TruncateRegressionTest,
        MSWDTestCase,
        # ReedRegressionTest,
        PearsonRegressionTest,
        NewYorkRegressionTest,
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
        ExperimentEditorPerformanceTestCase,
        ExperimentExecutorSyncTestCase,
        FrequencyTestCase,
        FrequencyTemplateTestCase,
        XYTestCase,
        PyScriptIntegrationTestCase,
        QueueMetadataPropagationTestCase,
        ExperimentIdentifierTestCase,
        RenumberAliquotTestCase,
        StatsResponsivenessTestCase,
        AutomatedRunStateMachineTestCase,
        ConditionalsTestCase,
        ParseConditionalsTestCase,
        ConditionalConfigurationTestCase,
        ConditionalQueueActionTestCase,
        IdentifierTestCase,
        CommentTemplaterTestCase,
        DataCollectionSyncTestCase,
        # ExternalPipette
        ExternalPipetteTestCase,
        # Processing
        MainViewValueReuseTestCase,
        IsotopeInvalidationTestCase,
        PlateauTestCase,
        RatioTestCase,
        AgeConverterTestCase,
        PyScriptRuntimeTestCase,
        # Pyscripts
        # WaitForTestCase,
        # InterpolationTestCase,
        # DocstrContextTestCase,
        # Spectrometer
        # MFTableTestCase,
        DiscreteMFTableTestCase,
        IntegrationTimeTestCase,
        NGXAcquisitionTestCase,
        # Stage
        StageMapTestCase,
        TransformTestCase,
    )

    for t in tests:
        suite.addTest(loader.loadTestsFromTestCase(t))

    return suite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
