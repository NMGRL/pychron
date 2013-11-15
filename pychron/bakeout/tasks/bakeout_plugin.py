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

#============= enthought library imports =======================
from traits.api import HasTraits, List
from traitsui.api import View, Item

from envisage.plugin import Plugin
from envisage.ui.tasks.task_factory import TaskFactory
from pychron.bakeout.tasks.bakeout_task import BakeoutTask
from pychron.bakeout.bakeout_manager import BakeoutManager
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
#============= standard library imports ========================
#============= local library imports  ==========================

class BakeoutPlugin(BaseTaskPlugin):

    def _tasks_default(self):
        ts = [TaskFactory(id='bakeout.main',
                        name='Main',
                        factory=self._bakeout_factory),
              ]
        return ts

    def _bakeout_factory(self):
        bm = BakeoutManager(application=self.application)
        bm.load()
        bt = BakeoutTask(bakeout=bm)
        return bt
#============= EOF =============================================
