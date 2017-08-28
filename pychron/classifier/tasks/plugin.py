# ===============================================================================
# Copyright 2017 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition

from pychron.classifier.isotope_classifier import IsotopeClassifier
from pychron.classifier.tasks.actions import TrainIsotopeClassifierAction
from pychron.dvc.dvc import DVC
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class ClassifierPlugin(BaseTaskPlugin):
    name = 'Classifier'

    # def start(self):
    #     super(ClassifierPlugin, self).start()
    #     dvc = self.application.get_service(DVC)
    #
    # def stop(self):
    #     pass

    def _service_offers_default(self):
        # p = {'dvc': self.dvc_factory()}
        # self.debug('DDDDD {}'.format(p))
        so = self.service_offer_factory(protocol=IsotopeClassifier,
                                        factory=IsotopeClassifier,
                                        properties={'dvc':  DVC(application=self.application)})

        return [so, ]

    # def _preferences_default(self):
    #     return self._preferences_factory('dvc')

    def _preferences_panes_default(self):
        return []

    # def _tasks_default(self):
    #     return [TaskFactory(id='pychron.experiment_repo.task',
    #                         name='Experiment Repositories',
    #                         factory=self._repo_factory)]

    def _task_extensions_default(self):
        actions = [SchemaAddition(factory=TrainIsotopeClassifierAction,
                                  path='MenuBar/tools.menu'),
                   ]

        return [TaskExtension(actions=actions), ]
# ============= EOF =============================================
