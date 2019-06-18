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
from __future__ import absolute_import

from traits.api import Event

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.graph.stacked_graph import StackedGraph
from pychron.graph.stacked_regression_graph import StackedRegressionGraph


class AnalysisGraph(Graph):
    rescale_event = Event
    figure_event = Event

    def get_rescale_actions(self):
        return [('Valid Analyses', 'rescale_to_valid', {})]

    def rescale_to_valid(self):
        self.rescale_event = 'valid'

    def rescale_x_axis(self):
        self.rescale_event = 'x'

    def rescale_y_axis(self):
        self.rescale_event = 'y'


class AnalysisStackedGraph(AnalysisGraph, StackedGraph):
    pass


class AnalysisStackedRegressionGraph(AnalysisGraph, StackedRegressionGraph):
    pass


class SpectrumGraph(AnalysisStackedGraph):
    # make_alternate_figure_event = Event

    def get_child_context_menu_actions(self):
        return [self.action_factory('Ideogram...', 'make_ideogram'),
                self.action_factory('Inverse Isochron...', 'make_inverse_isochron'),
                self.action_factory('Tag Non Plateau...', 'tag_non_plateau')]

    def tag_non_plateau(self):
        self.figure_event = ('tag', 'tag_non_plateau')

    def make_ideogram(self):
        self.figure_event = 'alternate_figure', 'Ideogram'

    def make_inverse_isochron(self):
        self.figure_event = 'alternate_figure', 'InverseIsochron'


class IdeogramGraph(AnalysisStackedGraph):

    def get_child_context_menu_actions(self):
        return [self.action_factory('Correlation...', 'make_correlation'),
                self.action_factory('Identify Peaks', 'identify_peaks')]

    def make_correlation(self):
        self.figure_event = ('correlation', (self.selected_plotid, self.selected_plot.y_axis.title))

    def identify_peaks(self):
        self.figure_event = ('identify_peaks', None)


class ReferencesGraph(AnalysisStackedRegressionGraph):

    def get_child_context_menu_actions(self):
        return [self.action_factory('Correlation...', 'make_correlation')]

    def make_correlation(self):
        self.figure_event = ('correlation', (self.selected_plot, self.selected_plot.y_axis.title))

# ============= EOF =============================================
