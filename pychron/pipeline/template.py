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

import yaml
from traits.api import HasTraits

from pychron.pipeline.nodes.data import DataNode, UnknownNode, DVCNode, InterpretedAgeNode, ListenUnknownNode
from pychron.pipeline.nodes.diff import DiffNode
from pychron.pipeline.nodes.find import FindNode
from pychron.pipeline.nodes.gain import GainCalibrationNode
from pychron.pipeline.nodes.geochron import GeochronNode
from pychron.pipeline.nodes.persist import PersistNode


class PipelineTemplate(HasTraits):
    def __init__(self, name, path, *args, **kw):
        super(PipelineTemplate, self).__init__(*args, **kw)

        self.name = name
        self.path = path

    def render(self, application, pipeline, bmodel, iabmodel, dvc, clear=False):
        # if first node is an unknowns node
        # render into template

        datanode = None
        try:
            node = pipeline.nodes[0]
            if isinstance(node, DataNode) and not isinstance(node, ListenUnknownNode):
                datanode = node
                datanode.visited = False
        except IndexError:
            pass

        if not datanode:
            datanode = UnknownNode(browser_model=bmodel, dvc=dvc)

        pipeline.nodes = []
        with open(self.path, 'r') as rfile:
            yd = yaml.load(rfile)

        nodes = yd['nodes']
        # print 'fafa', nodes
        for i, ni in enumerate(nodes):
            # print i, ni
            klass = ni['klass']
            if i == 0 and klass == 'UnknownNode':
                pipeline.nodes.append(datanode)
                continue

            node = self._node_factory(klass, ni)
            if isinstance(node, InterpretedAgeNode):
                node.trait_set(browser_model=iabmodel, dvc=dvc)
            elif isinstance(node, DVCNode):
                node.trait_set(browser_model=bmodel, dvc=dvc)
            elif isinstance(node, (FindNode, PersistNode, GainCalibrationNode)):
                node.trait_set(dvc=dvc)
            elif isinstance(node, DiffNode):
                recaller = application.get_service('pychron.mass_spec.mass_spec_recaller.MassSpecRecaller')
                node.trait_set(recaller=recaller)
            elif isinstance(node, GeochronNode):
                service = application.get_service('pychron.geochron.geochron_service.GeochronService')
                node.trait_set(service=service)

            node.finish_load()
            # elif isinstance(node, FitICFactorNode):
            #     node.set_detectors()

            pipeline.nodes.append(node)

    def _node_factory(self, klass, ni):
        mod = __import__('pychron.pipeline.nodes', fromlist=[klass])
        node = getattr(mod, klass)()
        node.pre_load(ni)
        node.load(ni)
        return node

# ============= EOF =============================================
