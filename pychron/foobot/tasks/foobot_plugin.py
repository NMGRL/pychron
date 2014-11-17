# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu
from traits.api import HasTraits, Button, Str, Int, Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup
#============= standard library imports ========================
#============= local library imports  ==========================



from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.foobot.tasks.actions import OpenFoobotAction
from pychron.foobot.tasks.foobot_task import FoobotTask


class FoobotPlugin(BaseTaskPlugin):
    def _my_task_extensions_default(self):
        return [TaskExtension(
                actions=[
                    SchemaAddition(id='foobot',
                                   path='MenuBar/help.menu',
                                   factory = OpenFoobotAction)])]
    def _tasks_default(self):
        return [TaskFactory(id='pychron.foobot.task',
                            factory=self._foobot_factory)]

    def _foobot_factory(self):
        return FoobotTask()
#============= EOF =============================================
