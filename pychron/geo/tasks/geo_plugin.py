# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.geo.processor import GeoProcessor
from pychron.geo.tasks.actions import ExportStratCanvasAction
from pychron.geo.tasks.geo_task import GeoTask


class GeoPlugin(BaseTaskPlugin):
    def _tasks_default(self):
        return [TaskFactory(id='pychron.geo', factory=self._geo_task_factory, name='Geo'), ]

    def _task_extensions_default(self):
        return [TaskExtension(actions=[SchemaAddition(id='export_strat_canvas',
                                                      factory=ExportStratCanvasAction,
                                                      absolute_position='last',
                                                      path='MenuBar/data.menu')])]

    def _geo_task_factory(self):
        return GeoTask(manager=GeoProcessor(application=self.application))

# ============= EOF =============================================

