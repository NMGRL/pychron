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
from traits.api import List, Str, Int, Enum, Float, Property, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.flux_views import VIEWS
from pychron.options.options import FigureOptions
from pychron.pychron_constants import FLUX_CONSTANTS, ERROR_TYPES


class FluxOptions(FigureOptions):
    subview_names = List(['Main', 'Appearance'], transient=True)
    color_map_name = Str('jet')
    marker_size = Int(5)
    levels = Int(50, auto_set=False, enter_set=True)

    error_kind = Str('SD')

    selected_decay = Enum(FLUX_CONSTANTS.keys())
    monitor_age = Float(28.201)
    lambda_k = Property(depends_on='selected_decay')

    model_kind = Enum('Plane', 'Bowl')
    predicted_j_error_type = Enum(*ERROR_TYPES)
    use_weighted_fit = Bool(False)
    monte_carlo_ntrials = Int(10)
    use_monte_carlo = Bool(False)
    monitor_sample_name = Str
    plot_kind = Enum('1D', '2D')

    def _selected_decay_changed(self, new):
        self.monitor_age = FLUX_CONSTANTS[new][4]

    def _get_lambda_k(self):
        dc = FLUX_CONSTANTS[self.selected_decay]
        return dc[0] + dc[2]

    def get_subview(self, name):
        name = name.lower()
        klass = self._get_subview(name)
        obj = klass(model=self)
        return obj

    def _get_subview(self, name):
        return VIEWS[name]

# ============= EOF =============================================
