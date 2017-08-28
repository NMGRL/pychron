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
from traitsui.menu import Action

from pychron.classifier.isotope_trainer import IsotopeTrainer


class TrainIsotopeClassifierAction(Action):
    name = 'Train'

    def perform(self, event):
        app = event.task.application
        dvc = app.get_service('pychron.dvc.dvc.DVC')
        print 'asdfasd', dvc
        trainer = IsotopeTrainer(dvc=dvc)
        trainer.train()
        # trainer.edit_traits(view=View('test'))

# ============= EOF =============================================
