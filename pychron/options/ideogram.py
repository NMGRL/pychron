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
from chaco.default_colormaps import color_map_name_dict
from traits.api import Int, Bool, Float, Property, on_trait_change, Enum, List, Dict, Button, Str, Color

from pychron.options.aux_plot import AuxPlot
from pychron.options.group.ideogram_group_options import IdeogramGroupOptions
from pychron.options.options import AgeOptions
from pychron.options.views.ideogram_views import VIEWS
from pychron.pychron_constants import NULL_STR, FONTS, SIZES, SIG_FIGS, MAIN, APPEARANCE, DISPLAY, GROUPS


class IdeogramAuxPlot(AuxPlot):
    names = List([NULL_STR, 'Analysis Number Nonsorted', 'Analysis Number',
                  'Radiogenic 40Ar', 'K/Ca', 'K/Cl', 'Mol K39', 'Signal K39', 'Ideogram'],
                 transient=True)
    _plot_names = List(['', 'analysis_number_nonsorted', 'analysis_number', 'radiogenic_yield',
                        'kca', 'kcl', 'moles_k39', 'signal_k39', 'relative_probability'],
                       transient=True)


class IdeogramOptions(AgeOptions):

    aux_plot_klass = IdeogramAuxPlot

    edit_label_format_button = Button
    edit_mean_format_button = Button

    mean_label_format = Str
    mean_label_display = Str
    # edit_label_format = Button
    # refresh_asymptotic_button = Button
    index_attrs = Dict(transient=True)
    probability_curve_kind = Enum('cumulative', 'kernel')
    mean_calculation_kind = Enum('weighted mean', 'kernel')
    use_centered_range = Bool
    use_static_limits = Bool
    xlow = Float
    xhigh = Float

    centered_range = Float(0.5)

    display_mean_indicator = Bool(True)
    display_mean = Bool(True)
    display_mean_mswd = Bool(True)
    display_mean_n = Bool(True)
    display_percent_error = Bool(True)
    # display_identifier_on_mean = Bool(False)
    # display_sample_on_mean = Bool(False)
    label_all_peaks = Bool(True)
    peak_label_sigfigs = Int
    peak_label_bgcolor = Color
    peak_label_border = Int
    peak_label_border_color = Color
    peak_label_bgcolor_enabled = Bool(False)
    aux_plot_name = 'Ideogram'

    use_asymptotic_limits = Bool
    # asymptotic_width = Float)
    asymptotic_height_percent = Float

    x_end_caps = Bool(False)
    y_end_caps = Bool(False)
    error_bar_nsigma = Enum(1, 2, 3)
    analysis_number_sorting = Enum('Oldest @Top', 'Youngest @Top')

    mean_indicator_font = Property
    mean_indicator_fontname = Enum(*FONTS)
    mean_indicator_fontsize = Enum(*SIZES)
    mean_sig_figs = Enum(*SIG_FIGS)

    use_cmap_analysis_number = Bool(False)
    cmap_analysis_number = Enum(list(color_map_name_dict.keys()))
    use_latest_overlay = Bool(False)
    show_results_table = Bool(False)

    group_options_klass = IdeogramGroupOptions

    _use_centered_range = Bool
    _use_asymptotic_limits = Bool
    _suppress_xlimits_clear = Bool

    def initialize(self):
        self.subview_names = [MAIN, 'Ideogram', APPEARANCE, 'Calculations', DISPLAY, GROUPS]

    def to_dict(self):
        d = super(IdeogramOptions, self).to_dict()
        aux_plots = self.to_dict_aux_plots()
        groups = self.to_dict_groups()

        d['aux_plots'] = aux_plots
        d['groups'] = groups
        return d

    def to_dict_aux_plots(self):
        return [ap.to_dict() for ap in self.aux_plots]

    def to_dict_groups(self):
        pass

    def to_dict_test(self, k):
        return k not in ('_suppress_xlimits_clear', 'aux_plots', 'groups', 'index_attrs')

    def get_plot_dict(self, group_id, subgroup_id):

        n = len(self.groups)
        gid = group_id % n
        fg = self.groups[gid]

        line_color = fg.line_color
        color = fg.color
        # if subgroup_id:
        #     rgb = color.red(), color.blue(), color.green()
        #     rgb = [c*0.9*subgroup_id for c in rgb]
        #     color.setRgb(*rgb)

        d = {'color': color,
             'edge_color': line_color,
             'edge_width': fg.line_width,
             'line_width': fg.line_width,
             'line_color': line_color}

        if fg.use_fill:
            color = fg.color.toRgb()
            color.setAlphaF(fg.alpha * 0.01)
            d['fill_color'] = color
            d['type'] = 'filled_line'

        return d

    # private
    def _get_subview(self, name):
        return VIEWS[name]

    # handlers
    @on_trait_change('use_static_limits, use_centered_range')
    def _handle_use_limits(self, new):
        # persist use asymptotic limits
        self._suppress_xlimits_clear = True
        if new:
            self._use_asymptotic_limits = self.use_asymptotic_limits
            self.trait_set(use_asymptotic_limits=False)
        else:
            self.trait_set(use_asymptotic_limits=self._use_asymptotic_limits)

        self._suppress_xlimits_clear = False

    def _use_asymptotic_limits_changed(self, new):
        # persist use_centered range
        if not self._suppress_xlimits_clear:
            if new:
                self._use_centered_range = self.use_centered_range
                self.trait_set(use_centered_range=False)
            else:
                self.trait_set(use_centered_range=self._use_centered_range)

    @on_trait_change('xlow, xhigh')
    def _handle_static_limits(self):
        for ap in self.aux_plots:
            ap.clear_xlimits()

    @on_trait_change('use_asymptotic_limits, asymptotic+, use_centered_range, centered_range, use_static_limits')
    def _handle_asymptotic(self, name, new):
        # if name.startswith('use') and not new:
        #     return

        if not self._suppress_xlimits_clear:
            for ap in self.aux_plots:
                ap.clear_xlimits()

    def _index_attr_changed(self):
        for ap in self.aux_plots:
            ap.clear_ylimits()

    def _edit_label_format_button_fired(self):
        from pychron.processing.label_maker import LabelTemplater, LabelTemplateView

        lm = LabelTemplater(label=self.analysis_label_display)
        lv = LabelTemplateView(model=lm)
        info = lv.edit_traits()
        if info.result:
            self.analysis_label_format = lm.formatter
            self.analysis_label_display = lm.label
            # self.refresh_plot_needed = True

    def _edit_mean_format_button_fired(self):
        from pychron.processing.label_maker import MeanLabelTemplater, MeanLabelTemplateView

        lm = MeanLabelTemplater(label=self.mean_label_display)
        lv = MeanLabelTemplateView(model=lm)
        info = lv.edit_traits()
        if info.result:
            self.mean_label_format = lm.formatter
            self.mean_label_display = lm.label

    def _get_mean_indicator_font(self):
        return '{} {}'.format(self.mean_indicator_fontname,
                              self.mean_indicator_fontsize)

    def _index_attrs_default(self):
        return {'uage': '01:Age',
                'uF': '02:Ar40*/Ar39k',
                'Ar40/Ar36': '03:Ar40/Ar36',
                'Ar40/Ar39': '04:Ar40/Ar39',
                'Ar40/Ar38': '05:Ar40/Ar38',
                'Ar39/Ar37': '06:Ar39/Ar37',
                'uAr40/Ar36': '07:uncor. Ar40/Ar36',
                'Ar40': '08:Ar40',
                'Ar39': '09:Ar39',
                'Ar38': '10:Ar38',
                'Ar37': '11:Ar37',
                'Ar36': '12:Ar36',
                'j': '13:J'}

# ============= EOF =============================================
