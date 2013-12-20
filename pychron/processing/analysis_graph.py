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
from traits.api import Event

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.graph.regression_graph import StackedRegressionGraph
from pychron.graph.stacked_graph import StackedGraph


class AnalysisGraph(Graph):
    tag=Event
    def get_child_context_menu_actions(self):
        return [self.action_factory('Set tag', '_set_tag')]

    def _set_tag(self):
        self.tag='foo'

class AnalysisStackedGraph(AnalysisGraph, StackedGraph):
    pass

class AnalysisStackedRegressionGraph(AnalysisGraph, StackedRegressionGraph):
    pass

#============= EOF =============================================

