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
from traits.api import Enum, Float, Bool, Button, Property, Int, on_trait_change, List
from traitsui.api import Item, HGroup, Group, VGroup, UItem, EnumEditor, InstanceEditor, spring

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.color_generators import colornames
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.plotters.options.age import AgeOptions
from pychron.processing.plotters.options.fill_group_editor import Fill, FillGroupEditor
from pychron.processing.plotters.options.plotter import FONTS, SIZES


class IdeogramOptions(AgeOptions):
    probability_curve_kind = Enum('cumulative', 'kernel')
    mean_calculation_kind = Enum('weighted mean', 'kernel')

    use_static_limits = Bool
    xlow = Float
    xhigh = Float

    _use_centered_range = Bool
    centered_range = Float(0.5)

    display_mean_indicator = Bool(True)
    display_mean = Bool(True)
    display_percent_error = Bool(True)
    plot_option_name = 'Ideogram'
    # index_attr = Enum('Age', 'Ar40*/Ar39k','Ar40/Ar36')
    #index_attr = String

    use_asymptotic_limits = Bool
    _use_asymptotic_limits = Bool
    _suppress_xlimits_clear = Bool

    asymptotic_width = Float
    asymptotic_percent = Float
    x_end_caps = Bool(False)
    y_end_caps = Bool(False)
    error_bar_nsigma = Enum(1, 2, 3)
    analysis_number_sorting = Enum('Oldest @Top', 'Youngest @Top')
    # analysis_label_format = String
    # analysis_label_display = String
    edit_label_format = Button

    mean_indicator_font = Property
    mean_indicator_fontname = Enum(*FONTS)
    mean_indicator_fontsize = Enum(*SIZES)

    mean_sig_figs = Int

    refresh_asymptotic_button = Button

    display_inset = Bool
    inset_location = Enum('Upper Right', 'Upper Left', 'Lower Right', 'Lower Left')
    inset_width = Int(160)
    inset_height = Int(100)

    # use_filled_line = Bool
    # fill_color = Color
    # fill_alpha = Range(0.0, 100.0)
    edit_group_fill_color_button = Button
    fill_groups = List
    fill_group = Property  #(trait=Fill)

    def get_fill_dict(self, group_id):
        n = len(self.fill_groups)
        gid = group_id % n
        fg = self.fill_groups[gid]
        if fg.use_filled_line:
            color = fg.color
            color.setAlphaF(fg.alpha * 0.01)
            return dict(fill_color=fg.color,
                        type='filled_line')
        else:
            return {}

    def _edit_group_fill_color_button_fired(self):
        eg = FillGroupEditor(fill_groups=self.fill_groups)
        info = eg.edit_traits()
        if info.result:
            self.refresh_plot_needed = True

    @on_trait_change('use_static_limits, use_centered_range')
    def _handle_use_limits(self, new):
        #persist use asymptotic limits
        self._suppress_xlimits_clear = True
        if new:
            self._use_asymptotic_limits = self.use_asymptotic_limits
            self.trait_set(use_asymptotic_limits=False)
        else:
            self.trait_set(use_asymptotic_limits=self._use_asymptotic_limits)

        self._suppress_xlimits_clear = False

    def _use_asymptotic_limits_changed(self, new):
        #persist use_centered range
        if not self._suppress_xlimits_clear:
            if new:
                self._use_centered_range = self.use_centered_range
                self.trait_set(use_centered_range=False)
            else:
                self.trait_set(use_centered_range=self._use_centered_range)

    def _refresh_asymptotic_button_fired(self):
        for ap in self.aux_plots:
            ap.clear_xlimits()
        self.refresh_plot_needed = True

    @on_trait_change('xlow, xhigh')
    def _handle_static_limits(self):
        for ap in self.aux_plots:
            ap.clear_xlimits()

    @on_trait_change('use_asymptotic_limits, asymptotic+, use_centered_range, centered_range, use_static_limits')
    def _handle_asymptotic(self, name, new):
        if name.startswith('use') and not new:
            return

        if not self._suppress_xlimits_clear:
            for ap in self.aux_plots:
                ap.clear_xlimits()

    def _index_attr_changed(self):
        for ap in self.aux_plots:
            ap.clear_ylimits()

    def _edit_label_format_fired(self):
        from pychron.processing.label_maker import LabelTemplater, LabelTemplateView
        lm = LabelTemplater(label=self.analysis_label_display)
        lv = LabelTemplateView(model=lm)
        info = lv.edit_traits()
        if info.result:
            self.analysis_label_format = lm.formatter
            self.analysis_label_display = lm.label

    def _get_groups(self):
        xgrp = VGroup(Item('index_attr',
                           editor=EnumEditor(values={'uage': '01:Age',
                                                     'uF': '02:Ar40*/Ar39k',
                                                     'Ar40/Ar36': '03:Ar40/Ar36',
                                                     'Ar40/Ar39': '04:Ar40/Ar39',
                                                     'Ar40/Ar38': '05:Ar40/Ar38',
                                                     'Ar39/Ar37': '06:Ar39/Ar37',
                                                     'Ar40': '07:Ar40',
                                                     'Ar39': '08:Ar39',
                                                     'Ar38': '09:Ar38',
                                                     'Ar37': '10:Ar37',
                                                     'Ar36': '11:Ar36', }),
                           label='X Value'),
                      HGroup(UItem('use_static_limits'),
                             Item('xlow', label='Min.',
                                  enabled_when='object.use_static_limits'),
                             Item('xhigh', label='Max.',
                                  enabled_when='object.use_static_limits'),
                             show_border=True,
                             label='Static Limits'),
                      HGroup(UItem('use_asymptotic_limits'),
                             Item('asymptotic_width', label='% Width',
                                  tooltip='Width of asymptotic section that is less than the Asymptotic %'),
                             Item('asymptotic_percent',
                                  tooltip='Percent of Max probability',
                                  label='% Height'),
                             icon_button_editor('refresh_asymptotic_button', 'refresh',
                                                enabled_when='object.use_asymptotic_limits',
                                                tooltip='Refresh plot with defined asymptotic limits'),
                             enabled_when='not object.use_centered_range and not object.use_static_limits',
                             show_border=True,
                             label='Asymptotic Limits'),
                      HGroup(UItem('use_centered_range'),
                             UItem('centered_range',
                                   enabled_when='object.use_centered_range'),
                             label='Center on fixed range',
                             show_border=True,
                             enabled_when='not object.use_static_limits'))

        g = Group(
            Item('probability_curve_kind',
                 width=-150,
                 label='Probability Curve Method'),
            Item('mean_calculation_kind',
                 width=-150,
                 label='Mean Calculation Method'),
            Item('error_calc_method',
                 width=-150,
                 label='Error Calculation Method'),
            Item('nsigma', label='Age Error NSigma'),
            HGroup(
                Item('include_j_error',
                     label='Include in Analyses'),
                Item('include_j_error_in_mean',
                     label='Include in Mean',
                     enabled_when='not include_j_error'),
                show_border=True, label='J Error'),

            Item('include_irradiation_error'),
            Item('include_decay_error'),
            show_border=True,
            label='Calculations')

        g2 = Group(VGroup(HGroup(Item('display_mean_indicator', label='Indicator'),
                                 Item('display_mean', label='Value',
                                      enabled_when='display_mean_indicator'),
                                 Item('display_percent_error', label='%Error',
                                      enabled_when='display_mean_indicator')),
                          HGroup(Item('mean_sig_figs', label='Mean'),
                                 show_border=True,
                                 label='SigFigs'),
                          show_border=True,
                          label='Mean'),
                   VGroup(Item('display_inset'),
                          Item('inset_location'),
                          HGroup(Item('inset_width', label='Width'),
                                 Item('inset_height', label='Height')),
                          show_border=True,
                          label='Inset'),
                   Item('label_box'),
                   Item('analysis_number_sorting', label='Analysis# Sort'),
                   HGroup(Item('analysis_label_display',
                               width=100,
                               style='readonly'),
                          icon_button_editor('edit_label_format', 'cog',
                                             tooltip='Open Label maker')),
                   HGroup(Item('show_info', label='Show'),
                          Item('show_mean_info', label='Mean', enabled_when='show_info'),
                          Item('show_error_type_info', label='Error Type', enabled_when='show_info'),
                          show_border=True,
                          label='Info'),
                   VGroup(UItem('fill_group', style='custom',
                                editor=InstanceEditor(view='simple_view')),
                          HGroup(icon_button_editor('edit_group_fill_color_button', 'cog'), spring),
                          show_border=True, label='Fill'),
                   # VGroup(HGroup(UItem('use_filled_line'),
                   #               Item('fill_color', enabled_when='use_filled_line')),
                   #        Item('fill_alpha'),
                   #        icon_button_editor('edit_group_fill_color_button', 'cog'),
                   #        label='Fill',
                   #        show_border=True),
                   show_border=True,
                   label='Display')

        egrp = VGroup(HGroup(Item('x_end_caps', label='X'),
                             Item('y_end_caps', label='Y'),
                             label='End Caps', ),
                      Item('error_bar_nsigma', label='NSigma'),
                      show_border=True,
                      label='Error Bars')
        main_grp = VGroup(self._get_title_group(),
                          xgrp,
                          g, g2, egrp, label='Main')

        orgp = Group(main_grp,
                     # label_grp,
                     # layout='tabbed',
                     label='Options')

        label_grp = VGroup(self._get_x_axis_group(),
                           self._get_y_axis_group(),
                           self._get_indicator_font_group(),
                           self._get_label_font_group(),
                           label='Fonts')
        return orgp, label_grp

    def _get_indicator_font_group(self):
        g = VGroup(HGroup(Item('mean_indicator_fontname', label='Mean Indicator'),
                          Item('mean_indicator_fontsize', show_label=False)),
                   HGroup(Item('error_info_fontname', label='Error Info'),
                          Item('error_info_fontsize', show_label=False)),
                   label='Info')
        return g

    def _get_mean_indicator_font(self):
        return '{} {}'.format(self.mean_indicator_fontname,
                              self.mean_indicator_fontsize)

    def _get_fill_group(self):
        return self.fill_groups[0]

    def _fill_groups_default(self):
        return [Fill(group_id=i,
                     color=colornames[i + 1],
                     alpha=100) for i in range(10)]

    def _get_dump_attrs(self):
        attrs = super(IdeogramOptions, self)._get_dump_attrs()
        return attrs + [
            'probability_curve_kind',
            'mean_calculation_kind',
            'error_calc_method',
            'xlow', 'xhigh',
            'use_static_limits',
            'use_centered_range', 'centered_range',
            'use_asymptotic_limits', 'asymptotic_width', 'asymptotic_percent',
            'display_mean', 'display_mean_indicator',
            'x_end_caps', 'y_end_caps', 'index_attr', 'error_bar_nsigma',
            'analysis_number_sorting',
            'display_percent_error',
            'mean_indicator_fontname',
            'mean_indicator_fontsize',
            'mean_sig_figs',
            'display_inset', 'inset_location', 'inset_width', 'inset_height',
            'fill_groups',
            'label_fontsize'
            # 'use_filled_line', 'fill_color', 'fill_alpha'
        ]

# ============= EOF =============================================
