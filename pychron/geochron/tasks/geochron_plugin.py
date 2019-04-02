# ===============================================================================
# Copyright 2016 ross
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

# ============= local library imports  ==========================
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
# ============= standard library imports ========================
from traits.api import List

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.geochron.geochron_service import GeochronService
from pychron.geochron.tasks.actions import UploadAction
from pychron.geochron.tasks.node import GeochronNode
from pychron.geochron.tasks.preferences import GeochronPreferencesPane
from pychron.pipeline.nodes import NodeFactory

GEOCHRON = """
required:
 - pychron.geochron.geochron_service.GeochronService
nodes:
 - klass: UnknownNode
 - klass: GeochronNode
"""


class GeochronPlugin(BaseTaskPlugin):
    id = 'pychron.geochron.plugin'

    node_factories = List(contributes_to='pychron.pipeline.node_factories')

    predefined_templates = List(contributes_to='pychron.pipeline.predefined_templates')

    def _node_factories_default(self):
        def geochron_factory():
            node = GeochronNode()
            service = self.application.get_service('pychron.geochron.geochron_service.GeochronService')
            node.trait_set(service=service)
            return node

        return [NodeFactory('GeochronNode', geochron_factory), ]

    def _predefined_templates_default(self):
        return [('Share', (('Geochron', GEOCHRON),))]

    def _help_tips_default(self):
        return ['More information about Geochron is located at http://geochron.org/']

    def _service_offers_default(self):
        so1 = self.service_offer_factory(factory=GeochronService,
                                         protocol=GeochronService)
        return [so1]

    def _preferences_panes_default(self):
        return [GeochronPreferencesPane]

    def _task_extensions_default(self):
        actions = [SchemaAddition(factory=UploadAction,
                                  path='MenuBar/data.menu')]
        ts = [TaskExtension(actions=actions)]
        return ts

# ============= EOF =============================================
