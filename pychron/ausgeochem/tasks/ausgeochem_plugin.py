# ===============================================================================
# Copyright 2024 Pychron Developers
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

from __future__ import absolute_import

from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import List

from pychron.ausgeochem.earthdata_service import AusGeochemEarthDataService
from pychron.ausgeochem.tasks.actions import UploadAusGeochemAction
from pychron.ausgeochem.tasks.node import AusGeochemNode
from pychron.ausgeochem.tasks.preferences import AusGeochemPreferencesPane
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.pipeline.nodes import NodeFactory

AUSGEOCHEM_TEMPLATE = """
required:
 - pychron.ausgeochem.earthdata_service.AusGeochemEarthDataService
nodes:
 - klass: UnknownNode
 - klass: AusGeochemNode
"""


class AusGeochemPlugin(BaseTaskPlugin):
    id = "pychron.ausgeochem.plugin"

    node_factories = List(contributes_to="pychron.pipeline.node_factories")
    predefined_templates = List(contributes_to="pychron.pipeline.predefined_templates")

    def _node_factories_default(self):
        def factory():
            node = AusGeochemNode()
            service = self.application.get_service(
                "pychron.ausgeochem.earthdata_service.AusGeochemEarthDataService"
            )
            if service is not None:
                node.trait_set(service=service)
            return node

        return [NodeFactory("AusGeochemNode", factory)]

    def _predefined_templates_default(self):
        return [("Share", (("AusGeochem", AUSGEOCHEM_TEMPLATE),))]

    def _help_tips_default(self):
        return ["AusGeochem EarthData help: https://app.ausgeochem.org"]

    def _service_offers_default(self):
        offer = self.service_offer_factory(
            factory=AusGeochemEarthDataService, protocol=AusGeochemEarthDataService
        )
        return [offer]

    def _preferences_panes_default(self):
        return [AusGeochemPreferencesPane]

    def _task_extensions_default(self):
        actions = [
            SchemaAddition(
                factory=UploadAusGeochemAction, path="MenuBar/data.menu"
            )
        ]
        return [TaskExtension(actions=actions)]


# ============= EOF =============================================
