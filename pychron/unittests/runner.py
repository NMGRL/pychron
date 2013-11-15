
from traits.etsconfig.etsconfig import ETSConfig
from pychron.paths import paths
from pychron.helpers.logger_setup import logging_setup
ETSConfig.toolkit = 'qt4'


paths.build('_dev')
logging_setup('unittests')

from .flat_file import FlatFileTest
# from .analysis import AnalysisTest
# from .magnet import MagnetTest
# from .motor import MotionProfilerTest
# from .pyscript import PyscriptDurationTest
# from .pyscript import RampTest
# from machine_vision import FocusTest
# from .loading import LoadingTest
# from .motor import LinearMapperTest
# from .lab_entry import LabEntryTest
# from .database import IsotopeTestCase
# from .experiment import ExperimentTest2
# from .experiment import ExecutorTest
# from .experiment import HumanErrorCheckerTest
# from .experiment_queue import QueueTest
# from .automated_run import AutomatedRunTest
# from .processing import FileSelectorTest
# from .processing import AutoFigureTest
# from .pyscript import PyscriptTest
# from .york_regression import YorkRegressionTest, NewYorkRegressionTest
# from .regression import NewYorkRegressionTest
# from .bayesian import BayesianTest
