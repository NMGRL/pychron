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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.graph.stacked_graph import StackedGraph
from pychron.graph.stacked_regression_graph import StackedRegressionGraph


class AnalysisGraph(Graph):
    pass
    # tag = Event
    # save_db_figure = Event
    # invalid = Event

    # def get_contextual_menu_save_actions(self):
    #     s = super(AnalysisGraph, self).get_contextual_menu_save_actions()
    #     s.extend([('Database', '_save_to_database', {})])
    #     return s
    #
    # def get_child_context_menu_actions(self):
    #     return [self.action_factory('Set tag', '_set_tag'),
    #             self.action_factory('Set INVALID', '_set_invalid')]
    #
    # def _save_to_database(self):
    #     print 'save to database'
    #     self.save_db_figure = True
    #

    def _set_tag(self):
        """
        open the tag dialog
        :return:
        """
        print 'set tag'
        self.tag = True

    def _set_invalid(self):
        print 'set invalid'
        self.invalid = True


class AnalysisStackedGraph(AnalysisGraph, StackedGraph):
    pass


class AnalysisStackedRegressionGraph(AnalysisGraph, StackedRegressionGraph):
    pass

# ============= EOF =============================================
