#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================
from traits.etsconfig.etsconfig import ETSConfig
from pychron.unittests.database import isotope_manager_factory
# from pychron.helpers import logger_setup
from pychron.helpers.logger_setup import logging_setup
from pychron.spectrometer.spectrometer_manager import SpectrometerManager
# from pychron.codetools.memory_usage import count_instances
from pychron.globals import globalv
ETSConfig.toolkit = 'qt4'


from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.experiment.automated_run.spec import AutomatedRunSpec
import os
from pychron.paths import paths
#============= enthought library imports =======================
from traits.api import HasTraits
from traitsui.api import View, Item
#============= standard library imports ========================
#============= local library imports  ==========================
from guppy import hpy
from pychron.experiment.tasks.experiment_task import ExperimentEditorTask
from pychron.experiment.experiment_executor import ExperimentExecutor
def run():
    hp = hpy()

    globalv.experiment_debug = True
#     t = ExperimentEditorTask()
#     p = os.path.join(paths.experiment_dir, 'demo.txt')
#     t._open_experiment(p)


    q = ExperimentQueue(delay_before_analyses=0,
                        delay_between_analyses=0)
    q.automated_runs = [
                        AutomatedRunSpec(
                                         labnumber='61312',
                                         duration=2.0,
                                         extraction_script='pause',
                                         measurement_script='air',
                                         mass_spectrometer='jan'
                                         ),
                        AutomatedRunSpec(
                                         labnumber='61312',
                                         duration=2.0,
                                         extraction_script='pause',
                                         measurement_script='air',
                                         mass_spectrometer='jan'
                                         ),
                        AutomatedRunSpec(
                                         labnumber='61312',
                                         duration=2.0,
                                         extraction_script='pause',
                                         measurement_script='air',
                                         mass_spectrometer='jan'
                                         ),
                        AutomatedRunSpec(
                                         labnumber='61312',
                                         duration=2.0,
                                         extraction_script='pause',
                                         measurement_script='air',
                                         mass_spectrometer='jan'
                                         ),
                        AutomatedRunSpec(
                                         labnumber='61312',
                                         duration=2.0,
                                         extraction_script='pause',
                                         measurement_script='air',
                                         mass_spectrometer='jan'
                                         )

                        ]

    dbman = isotope_manager_factory()
    specman = SpectrometerManager()
    specman.load()

    ex = ExperimentExecutor(db=dbman.db,
                            spectrometer_manager=specman,
                            extraction_line_manager='',
                            executable=True,

                            )
    ex.monitor = None
    ex.experiment_queues = [q, ]
    ex.experiment_queue = q
    hp.setrelheap()
    t = ex.execute()
    t.join()
#     count_instances(group='sqlalchemy')

    return hp

log = False
def main():
    paths.build('_dev')

    global log
    if not log:
        logging_setup('heapy')
        log = True

    return run()





if __name__ == '__main__':
    main()
#============= EOF =============================================
