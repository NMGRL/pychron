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
from traits.api import Str, Int, Enum, Property, Bool, Float

from pychron.options.aux_plot import AuxPlot
from pychron.options.options import FigureOptions
from pychron.pychron_constants import FLUX_CONSTANTS, ERROR_TYPES, MAIN, APPEARANCE


class BaseFluxOptions(FigureOptions):
    color_map_name = Str('jet')
    marker_size = Int(5)
    levels = Int(50, auto_set=False, enter_set=True)
    plot_kind = Enum('1D', '2D', 'Grid')
    use_weighted_fit = Bool(False)
    monte_carlo_ntrials = Int(10)
    use_monte_carlo = Bool(False)
    position_error = Float
    predicted_j_error_type = Enum(*ERROR_TYPES)


class FluxOptions(BaseFluxOptions):
    error_kind = Enum(*ERROR_TYPES)

    selected_decay = Enum(list(FLUX_CONSTANTS.keys()))
    lambda_k = Property(depends_on='selected_decay')
    monitor_age = Property(depends_on='selected_decay')
    model_kind = Enum('Plane', 'Bowl', 'Weighted Mean', 'Matching', 'Bracketing')
    flux_scalar = Float(1000)

    monitor_sample_name = Str

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE]

    def _get_lambda_k(self):
        dc = FLUX_CONSTANTS[self.selected_decay]
        return dc['lambda_b'][0] + dc['lambda_ec'][0]

    def _get_monitor_age(self):
        dc = FLUX_CONSTANTS[self.selected_decay]
        return dc['monitor_age']

    def _get_subview(self, name):
        from pychron.options.views.flux_views import VIEWS
        return VIEWS[name]


class FluxVisualizationOptions(BaseFluxOptions):
    model_kind = Enum('Plane', 'Bowl')

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE]

    def _get_subview(self, name):
        from pychron.options.views.flux_visualization_views import VIEWS
        return VIEWS[name]


class VerticalFluxAuxPlot(AuxPlot):
    name = 'Height (cm)'


class VerticalFluxOptions(FigureOptions):

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE]

    def get_plotable_aux_plots(self):
        return [VerticalFluxAuxPlot()]

    def _get_subview(self, name):
        from pychron.options.views.vertical_flux_views import VIEWS
        return VIEWS[name]
# ============= EOF =============================================
