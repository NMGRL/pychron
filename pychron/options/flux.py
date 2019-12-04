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
from traits.api import Str, Int, Enum, Property, Bool, Float, HasTraits
from uncertainties import ufloat

from pychron.options.aux_plot import AuxPlot
from pychron.options.options import FigureOptions
from pychron.pychron_constants import FLUX_CONSTANTS, ERROR_TYPES, MAIN, APPEARANCE, FLUX_MODEL_KINDS


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


class MonitorMixin(HasTraits):
    error_kind = Enum(*ERROR_TYPES)

    selected_monitor = Enum(list(FLUX_CONSTANTS.keys()))
    lambda_k = Property(depends_on='selected_monitor')
    monitor_age = Property(depends_on='selected_monitor')
    monitor_name = Property(depends_on='selected_monitor')
    monitor_material = Property(depends_on='selected_monitor')

    def _get_lambda_k(self):
        dc = FLUX_CONSTANTS[self.selected_monitor]
        b = ufloat(*dc['lambda_b'])
        ec = ufloat(*dc['lambda_ec'])
        return b+ec

    def _get_monitor_name(self):
        return FLUX_CONSTANTS[self.selected_monitor].get('monitor_name', '')

    def _get_monitor_age(self):
        return FLUX_CONSTANTS[self.selected_monitor].get('monitor_age', 0)

    def _get_monitor_material(self):
        return FLUX_CONSTANTS[self.selected_monitor].get('monitor_material', '')


class FluxOptions(BaseFluxOptions, MonitorMixin):

    model_kind = Enum(FLUX_MODEL_KINDS)
    flux_scalar = Float(1000)
    n_neighbors = Int(2)

    least_squares_fit = Enum('Linear', 'Parabolic', 'Cubic', 'Quartic')
    one_d_axis = Enum('X', 'Y')

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE]

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
    name = 'Height (mm)'


class VerticalFluxOptions(FigureOptions, MonitorMixin):

    use_j = Bool
    use_f_enabled = Bool

    @property
    def x_title(self):
        t = 'J'
        if self.use_f_enabled:
            t = 'J' if self.use_j else '<sup>40</sup>Ar*/<sup>Ar</sub>39<sub>K</sub>'
        return t

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE]

    def get_plotable_aux_plots(self):
        return [VerticalFluxAuxPlot()]

    def _get_subview(self, name):
        from pychron.options.views.vertical_flux_views import VIEWS
        return VIEWS[name]
# ============= EOF =============================================
