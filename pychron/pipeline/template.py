# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import HasTraits

# ============= standard library imports ========================
import yaml
# ============= local library imports  ==========================
from pychron.pipeline.nodes.data import DataNode
from pychron.pipeline.nodes.find import FindReferencesNode
from pychron.pipeline.nodes.persist import PersistNode


class PipelineTemplate(HasTraits):
    def __init__(self, name, path, *args, **kw):
        super(PipelineTemplate, self).__init__(*args, **kw)

        self.name = name
        self.path = path

    def render(self, pipeline, bmodel, dvc, clear=False):
        # if first node is an unknowns node
        # render into template

        datanode = None
        try:
            node = pipeline.nodes[0]
            if isinstance(node, DataNode):
                datanode = node
                datanode.visited = False
        except IndexError:
            pass

        pipeline.nodes = []
        with open(self.path, 'r') as rfile:
            nodes = yaml.load(rfile)

        for i, ni in enumerate(nodes):
            klass = ni['klass']
            if i == 0 and klass == 'UnknownNode':
                pipeline.nodes.append(datanode)
                continue

            node = self._node_factory(klass, ni)
            if isinstance(node, DataNode):
                node.trait_set(browser_model=bmodel, dvc=dvc)
            elif isinstance(node, (FindReferencesNode, PersistNode)):
                node.trait_set(dvc=dvc)
            # elif isinstance(node, FitICFactorNode):
            #     node.set_detectors()

            pipeline.nodes.append(node)

    def _node_factory(self, klass, ni):
        mod = __import__('pychron.pipeline.nodes', fromlist=[klass])
        node = getattr(mod, klass)()
        node.load(ni)
        return node


ICFACTOR = """
- klass: UnknownNode
- klass: FindReferencesNode
  threshold: 10
  analysis_type: Blank Unknown
- klass: ReferenceNode
- klass: FitICFactorNode
  fits:
    - numerator: H1
      denominator: AX
      standard_ratio: 295.5
      analysis_type: Air
- klass: ICFactorPersistNode
"""

ISOEVO = """
- klass: UnknownNode
- klass: FitIsotopeEvolutionNode
- klass: IsotopeEvolutionPersistNode
"""

BLANKS = """
- klass: UnknownNode
- klass: FindReferencesNode
  threshold: 10
  analysis_type: Blank Unknown
- klass: ReferenceNode
- klass: FitBlanksNode
- klass: BlanksPersistNode
"""

# ============= EOF =============================================
