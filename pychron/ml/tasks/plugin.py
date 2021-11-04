# ===============================================================================
# Copyright 2019 Jake Ross
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
from traits.api import List

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.ml.nodes.cluster import ClusterNode
from pychron.ml.nodes.data import CSVClusterNode
from pychron.ml.tasks.preferences import MachineLearningPreferencesPane
from pychron.pipeline.nodes import NodeFactory

# ============= standard library imports ========================
# ============= local library imports  ==========================

CLUSTER = """required:
nodes:
 - klass: UnknownNode
 - klass: ClusterNode
 """

CSVCLUSTER = """
required:
nodes:
  - klass: CSVClusterNode
  - klass: ClusterNode
"""


class MachineLearningPlugin(BaseTaskPlugin):
    id = "pychron.machinelearning.plugin"
    node_factories = List(contributes_to="pychron.pipeline.node_factories")
    predefined_templates = List(contributes_to="pychron.pipeline.predefined_templates")
    pipeline_group_icon_map = List(
        contributes_to="pychron.pipeline.pipeline_group_icon_map"
    )

    def _service_offers_default(self):
        """ """
        # so = self.service_offer_factory()
        return []

    def _node_factories_default(self):
        def cluster_factory():
            node = ClusterNode()
            # service = self.application.get_service('pychron.geochron.geochron_service.GeochronService')
            # node.trait_set(service=service)
            return node

        return [
            NodeFactory("ClusterNode", cluster_factory),
            NodeFactory("CSVClusterNode", CSVClusterNode),
        ]

    def _pipeline_group_icon_map_default(self):
        return [("ML", "bricks")]

    def _predefined_templates_default(self):
        return [("ML", (("Cluster", CLUSTER), ("CSV Cluster", CSVCLUSTER)))]

    # def _preferences_default(self):
    #     return ['file://']
    #
    # def _task_extensions_default(self):
    #
    #     return [TaskExtension(SchemaAddition)]
    # def _tasks_default(self):
    #     return [TaskFactory(factory=self._task_factory,
    #                         protocol=FurnaceTask)]

    def _preferences_panes_default(self):
        return [MachineLearningPreferencesPane]


# ============= EOF =============================================
