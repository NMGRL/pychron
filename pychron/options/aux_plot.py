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
from traits.api import (
    HasTraits,
    Str,
    Int,
    Bool,
    Float,
    Property,
    on_trait_change,
    Dict,
    Tuple,
    Enum,
    List,
    Any,
    Trait,
    Button,
    Color,
)

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import FilterPredicate
from pychron.pychron_constants import NULL_STR


def has_limits(lims):
    return lims is not None and lims[0] != lims[1]


YTITLES = {
    "Ar36": "<sup>36</sup>Ar<sub>tot</sub>(fA)",
    "Ar40": "<sup>40</sup>Ar<sub>tot</sub>(fA)",
    "uAr40/Ar36": "noncor. <sup>40</sup>Ar/<sup>36</sup>Ar",
    "Ar40/Ar36": "<sup>40</sup>Ar/<sup>36</sup>Ar",
    "icf_40_36": "ifc <sup>40</sup>Ar/<sup>36</sup>Ar",
    "radiogenic_yield": "%<sup>40</sup>Ar*",
    "extract_value": "Extract Value",
    "kcl": "K/Cl",
    "clk": "Cl/K",
    "kca": "K/Ca",
    "k39": "<sup>39</sup>Ar<sub>K</sub>(fA)",
    "moles_k39": "<sup>39</sup>Ar<sub>K</sub>(mol)",
    "Analysis Number": "Analysis #",
    "Analysis Number Nonsorted": "A# Nonsorted",
}


class AuxPlot(HasTraits):
    names = List(transient=True)
    _plot_names = List(transient=True)

    clear_ylimits_button = Button

    save_enabled = Bool
    plot_enabled = Bool
    name = Str(NULL_STR)
    plot_name = Property(Str, depends_on="name")
    scale = Enum("linear", "log")
    scalar = Float(1.0)
    height = Int(100, enter_set=True, auto_set=False)
    x_error = Bool(False)
    y_error = Bool(False)
    ytitle_visible = Bool(True)
    ytick_visible = Bool(True)
    show_labels = Bool(False)
    y_axis_right = Bool(False)
    yticks_both_sides = Bool(True)
    ytitle = Str

    use_sparse_yticks = Bool(True)
    sparse_yticks_step = Int(2)
    ytick_interval = Trait("auto", "auto", Float)

    filter_str = FilterPredicate
    sigma_filter_n = Int
    has_filter = Property(depends_on="filter_str, sigma_filter_n")
    filter_str_tag = Enum(("Omit", "Outlier", "Invalid"))
    sigma_filter_tag = Enum(("Omit", "Outlier", "Invalid"))

    normalize = None
    use_time_axis = False
    initialized = False

    ymin = Float
    ymax = Float
    xmin = Float
    xmax = Float

    ylimits = Tuple(Float, Float, transient=True)
    xlimits = Tuple(Float, Float, transient=True)

    overlay_positions = Dict(transient=True)
    _has_ylimits = Bool(False, transient=True)
    _has_xlimits = Bool(False, transient=True)

    marker = Str("circle")
    marker_size = Float(2)
    marker_color = Color("black")

    calculated_ymax = Any(transient=True)
    calculated_ymin = Any(transient=True)

    use_integer_ticks = False

    def get_ytitle(self, k):
        t = self.ytitle
        if not t:
            t = YTITLES.get(k, "***")
        return t

    def to_dict(self):
        keys = [k for k in self.traits(transient=False)]
        return {key: getattr(self, key) for key in keys}

    def set_overlay_position(self, k, v):
        self.overlay_positions[k] = v

    def has_xlimits(self):
        return self._has_xlimits or has_limits(self.xlimits)

    def has_ylimits(self):
        return self._has_ylimits or has_limits(self.ylimits)

    @on_trait_change("clear_ylimits_button")
    def clear_ylimits(self):
        self.ymin, self.ymax = 0, 0
        self.ylimits = (self.ymin, self.ymax)
        self._has_ylimits = has_limits(self.ylimits)

    def clear_xlimits(self):
        self.xmin, self.xmax = 0, 0
        self.xlimits = (self.xmin, self.xmax)
        self._has_xlimits = has_limits(self.xlimits)

    def _name_changed(self):
        if self.initialized:
            if self.name and self.name != NULL_STR:
                self.plot_enabled = True

    def _get_plot_name(self):
        if self._plot_names and self.name in self.names:
            try:
                return self._plot_names[self.names.index(self.name)]
            except IndexError:
                return ""
        else:
            return self.name

    def _set_has_filter(self, v):
        pass

    def _get_has_filter(self):
        return self.filter_str or self.sigma_filter_n

# ============= EOF =============================================
