# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Bool, Enum, String, Property, List, on_trait_change, Event
from traitsui.api import VGroup, UItem
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.color_generators import colornames
# from pychron.processing.plotters.options.plotter import PlotterOptions, FONTS, SIZES
from pychron.processing.plotters.options.figure_plotter_options import FigurePlotterOptions, FONTS, SIZES
from pychron.pychron_constants import ERROR_TYPES


class GroupablePlotterOptions(FigurePlotterOptions):
    groups = List
    group = Property
    group_editor_klass = None
    options_klass = None
    refresh_colors = Event

    def get_group_colors(self):
        return [gi.color for gi in self.groups]

    def _get_group(self):
        if self.groups:
            return self.groups[0]

    def get_group(self, gid):
        n = len(self.groups)
        return self.groups[gid % n]

    @on_trait_change('groups:edit_button')
    def _handle_edit_groups(self):
        eg = self.group_editor_klass(option_groups=self.groups)
        info = eg.edit_traits()
        if info.result:
            self.refresh_plot_needed = True

    def _groups_default(self):
        if self.options_klass:
            return [self.options_klass(color=ci,
                                       line_color=ci,
                                   group_id=i) for i, ci in enumerate(colornames)]
        else:
            return []


class AgeOptions(GroupablePlotterOptions):
    include_j_error = Bool(False)
    include_j_error_in_mean = Bool(True)
    error_calc_method = Enum(*ERROR_TYPES)


    include_sample_in_legend = Bool(False)
    legend_location = Enum('Upper Right', 'Upper Left', 'Lower Left', 'Lower Right')

    include_irradiation_error = Bool(True)
    include_decay_error = Bool(False)
    nsigma = Enum(1, 2, 3)
    show_info = Bool(True)
    show_mean_info = Bool(True)
    show_error_type_info = Bool(True)
    label_box = Bool(False)

    index_attr = String('uage')
    use_static_limits = False

    analysis_label_format = String
    analysis_label_display = String

    error_info_font = Property
    error_info_fontname = Enum(*FONTS)
    error_info_fontsize = Enum(*SIZES)

    label_font = Property
    label_fontname = Enum(*FONTS)
    label_fontsize = Enum(*SIZES)

    use_centered_range = Bool

    def make_legend_key(self, ident, sample):
        key = ident
        if self.include_sample_in_legend:
            key = '{}({})'.format(sample, ident)
        return key

    def _include_j_error_changed(self, new):
        if new:
            self.include_j_error_in_mean = False

    def _get_label_font(self):
        return '{} {}'.format(self.label_fontname, self.label_fontsize)

    def _get_error_info_font(self):
        return '{} {}'.format(self.error_info_fontname,
                              self.error_info_fontsize)

    def _get_label_font_group(self):
        g = VGroup(UItem('label_fontsize'),
                   show_border=True,
                   label='Labels')
        return g

    def _get_dump_attrs(self):
        attrs = super(AgeOptions, self)._get_dump_attrs()
        attrs += ['include_j_error',
                  'include_j_error_in_mean',
                  'include_irradiation_error',
                  'include_decay_error',
                  'nsigma', 'label_box',
                  'error_calc_method',
                  'include_legend',
                  'include_sample_in_legend',
                  'show_info', 'show_mean_info', 'show_error_type_info',
                  'analysis_label_display',
                  'analysis_label_format',
                  'error_info_fontname',
                  'error_info_fontsize', 'label_fontsize',
                  'groups']
        return attrs


# ============= EOF =============================================
