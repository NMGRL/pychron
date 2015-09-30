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
from traits.api import HasTraits, Str, Int, Bool, \
    Float, Property, on_trait_change, Dict, Tuple, Enum, List
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import FilterPredicate
from pychron.pychron_constants import NULL_STR


class AuxPlot(HasTraits):
    names = List
    _plot_names = List

    save_enabled = Bool
    plot_enabled = Bool
    name = Str(NULL_STR)
    plot_name = Property(Str, depends_on='name')
    scale = Enum('linear', 'log')
    height = Int(100, enter_set=True, auto_set=False)
    x_error = Bool(False)
    y_error = Bool(False)
    ytitle_visible = Bool(True)
    ytick_visible = Bool(True)
    show_labels = Bool(False)

    filter_str = FilterPredicate
    sigma_filter_n = Int
    has_filter = Property(depends_on='filter_str, sigma_filter_n')
    filter_str_tag = Enum(('Omit', 'Outlier', 'Invalid'))
    sigma_filter_tag = Enum(('Omit', 'Outlier', 'Invalid'))

    normalize = None
    use_time_axis = False
    initialized = False

    ymin = Float
    ymax = Float

    ylimits = Tuple(Float, Float, transient=True)
    xlimits = Tuple(Float, Float, transient=True)

    overlay_positions = Dict(transient=True)
    _has_ylimits = Bool(False, transient=True)
    _has_xlimits = Bool(False, transient=True)

    # enabled = True

    marker = Str('circle')
    marker_size = Float(2)

    _suppress = False

    def to_dict(self):
        keys = [k for k in self.traits(transient=False)]
        return {key: getattr(self, key) for key in keys}

    @on_trait_change('ylimits')
    def _handle_ylimits(self, new):
        self._suppress = True
        self.ymin = new[0]
        self.ymax = new[1]
        self._suppress = False

    @on_trait_change('ymin, ymax')
    def _handle_ymin_max(self, name, new):
        if self._suppress:
            return

        self._has_ylimits = True
        self.ylimits = (self.ymin, self.ymax)

    def set_overlay_position(self, k, v):
        self.overlay_positions[k] = v

    def has_xlimits(self):
        return self._has_xlimits or (self.xlimits is not None and self.xlimits[0] != self.xlimits[1])

    def has_ylimits(self):
        return self._has_ylimits or (self.ylimits is not None and self.ylimits[0] != self.ylimits[1])

    def clear_ylimits(self):
        self._has_ylimits = False
        self.ylimits = (0, 0)

    def clear_xlimits(self):
        self._has_xlimits = False
        self.xlimits = (0, 0)

    def _name_changed(self):
        # if self.initialized:
        if self.name and self.name != NULL_STR:
            self.plot_enabled = True

    def _get_plot_name(self):

        if self._plot_names and self.name in self.names:
            return self._plot_names[self.names.index(self.name)]
        else:
            return self.name

    def _set_has_filter(self, v):
        pass

    def _get_has_filter(self):
        return self.filter_str or self.sigma_filter_n
# ============= EOF =============================================
