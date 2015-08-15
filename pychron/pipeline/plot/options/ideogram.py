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
from matplotlib.cm import cmap_d
from traits.api import Enum, Float, Bool, Button, Property, Int, on_trait_change
from traitsui.api import Item, HGroup, Group, VGroup, UItem, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
# from pychron.pipeline.plot.options import AgeOptions
from pychron.pipeline.plot.options.age import AgeOptions
from pychron.pipeline.plot.options.base import dumpable
# from pychron.pipeline.plot.options import FONTS, SIZES
# from pychron.pipeline.plot.options import IdeogramGroupEditor, IdeogramGroupOptions
from pychron.pipeline.plot.options.figure_plotter_options import FONTS
from pychron.pipeline.plot.options.figure_plotter_options import SIZES
from pychron.pipeline.plot.options.ideogram_group_options import IdeogramGroupEditor
from pychron.pipeline.plot.options.ideogram_group_options import IdeogramGroupOptions


class IdeogramOptions(AgeOptions):
    edit_label_format = Button
    refresh_asymptotic_button = Button

    probability_curve_kind = dumpable(Enum('cumulative', 'kernel'))
    mean_calculation_kind = dumpable(Enum('weighted mean', 'kernel'))
    use_centered_range = dumpable(Bool)
    use_static_limits = dumpable(Bool)
    xlow = dumpable(Float)
    xhigh = dumpable(Float)

    centered_range = dumpable(Float, 0.5)

    display_mean_indicator = dumpable(Bool, True)
    display_mean = dumpable(Bool, True)
    display_percent_error = dumpable(Bool, True)
    aux_plot_name = 'Ideogram'

    use_asymptotic_limits = dumpable(Bool)
    # asymptotic_width = dumpable(Float)
    asymptotic_height_percent = dumpable(Float)

    x_end_caps = dumpable(Bool, False)
    y_end_caps = dumpable(Bool, False)
    error_bar_nsigma = dumpable(Enum, 1, 2, 3)
    analysis_number_sorting = dumpable(Enum, 'Oldest @Top', 'Youngest @Top')

    # mean_indicator_font = Font
    mean_indicator_font = Property
    mean_indicator_fontname = dumpable(Enum, *FONTS)
    mean_indicator_fontsize = dumpable(Enum, *SIZES)
    mean_sig_figs = dumpable(Int)

    display_inset = dumpable(Bool)
    inset_location = dumpable(Enum, 'Upper Right', 'Upper Left', 'Lower Right', 'Lower Left')
    inset_width = dumpable(Int, 160)
    inset_height = dumpable(Int, 100)

    use_cmap_analysis_number = dumpable(Bool, False)
    cmap_analysis_number = dumpable(Enum, *[m for m in cmap_d if not m.endswith("_r")])
    use_latest_overlay = dumpable(Bool, False)

    group_editor_klass = IdeogramGroupEditor
    options_klass = IdeogramGroupOptions

    _use_centered_range = Bool
    _use_asymptotic_limits = Bool
    _suppress_xlimits_clear = Bool

    def get_plot_dict(self, group_id):
        # return {}

        n = len(self.groups)
        gid = group_id % n
        fg = self.groups[gid]
        d = {'color': fg.line_color,
             'edge_color': fg.line_color,
             'edge_width': fg.line_width,
             'line_width': fg.line_width,
             'line_color': fg.line_color}

        if fg.use_fill:
            color = fg.color
            color.setAlphaF(fg.alpha * 0.01)
            d['fill_color'] = fg.color
            d['type'] = 'filled_line'
        return d

        # if fg.use_filled_line:
        # color = fg.color
        # color.setAlphaF(fg.alpha * 0.01)
        # return dict(fill_color=fg.color,
        #                 type='filled_line')
        # else:
        #     return {}

    # def _edit_group_fill_color_button_fired(self):
    # eg = FillGroupEditor(fill_groups=self.fill_groups)
    # info = eg.edit_traits()
    # if info.result:
    #         self.refresh_plot_needed = True

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
            self.refresh_plot_needed = True

    def _get_groups(self):
        xgrp = VGroup(Item('index_attr',
                           editor=EnumEditor(values={'uage': '01:Age',
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
                                                     'Ar36': '12:Ar36', }),
                           label='X Value'),
                      HGroup(UItem('use_static_limits'),
                             Item('xlow', label='Min.',
                                  enabled_when='object.use_static_limits'),
                             Item('xhigh', label='Max.',
                                  enabled_when='object.use_static_limits'),
                             show_border=True,
                             label='Static Limits'),
                      HGroup(UItem('use_asymptotic_limits'),
                             # Item('asymptotic_width', label='% Width',
                             #      tooltip='Width of asymptotic section that is less than the Asymptotic %'),
                             Item('asymptotic_height_percent',
                                  tooltip='Percent of Max probability',
                                  label='% Height'),
                             # icon_button_editor('refresh_asymptotic_button', 'refresh',
                             #                    enabled_when='object.use_asymptotic_limits',
                             #                    tooltip='Refresh plot with defined asymptotic limits'),
                             enabled_when='not object.use_centered_range and not object.use_static_limits',
                             show_border=True,
                             label='Asymptotic Limits'),
                      HGroup(UItem('use_centered_range'),
                             UItem('centered_range',
                                   enabled_when='object.use_centered_range'),
                             label='Center on fixed range',
                             show_border=True,
                             enabled_when='not object.use_static_limits'),
                      HGroup(UItem('use_xpad'),
                             Item('xpad', label='Pad', enabled_when='use_xpad'),
                             Item('xpad_as_percent',
                                  tooltip='Treat Pad as a percent of the nominal width, otherwise Pad is in Ma. '
                                          'e.g if width=10 Ma, Pad=0.5 '
                                          'the final width will be 10 + (10*0.5)*2 = 20 Ma.',
                                  enabled_when='use_xpad',
                                  label='%'),
                             label='X Pad',
                             show_border=True),
                      show_border=True,
                      label='X')

        calcgrp = Group(
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

        errbar_grp = VGroup(HGroup(Item('x_end_caps', label='X End Caps'),
                                   Item('y_end_caps', label='Y End Caps'),
                                   Item('error_bar_nsigma', label='NSigma')),
                            show_border=True,
                            label='Error Bars')

        an_grp = VGroup(Item('analysis_number_sorting', label='Analysis# Sort'),
                        Item('use_cmap_analysis_number'),
                        Item('cmap_analysis_number'),
                        Item('use_latest_overlay'), show_border=True, label='Analysis #')
        label_grp = VGroup(
            HGroup(Item('label_box'),
                   Item('analysis_label_display',
                        label='Label Format',
                        width=100,
                        style='readonly'),
                   icon_button_editor('edit_label_format', 'cog',
                                      tooltip='Open Label maker')),
            self._get_label_font_group(),
            show_border=True, label='Label')
        inset_grp = VGroup(HGroup(Item('display_inset', label='Use'),
                                  Item('inset_location', label='Location'),
                                  Item('inset_width', label='Width'),
                                  Item('inset_height', label='Height')),
                           show_border=True,
                           label='Inset')
        mean_grp = VGroup(HGroup(Item('display_mean_indicator', label='Indicator'),
                                 Item('display_mean', label='Value',
                                      enabled_when='display_mean_indicator'),
                                 Item('display_percent_error', label='%Error',
                                      enabled_when='display_mean_indicator'),
                                 Item('mean_sig_figs', label='SigFigs')),
                          self._get_indicator_font_group(),
                          show_border=True,
                          label='Mean')
        info_grp = HGroup(Item('show_info', label='Show'),
                          Item('show_mean_info', label='Mean', enabled_when='show_info'),
                          Item('show_error_type_info', label='Error Type', enabled_when='show_info'),
                          show_border=True,
                          label='Info')

        display_grp = Group(mean_grp,
                            an_grp,
                            inset_grp,
                            label_grp,
                            info_grp,
                            errbar_grp,
                            show_border=True,
                            label='Display')

        optgrp = VGroup(self._get_title_group(),
                        HGroup(xgrp, calcgrp),

                        # HGroup(xgrp, Tabbed(grp_grp, g,g2,egrp)),
                        # HGroup(g, g2, egrp),

                        label='Options')
        # axis_grp = VGroup(self._get_x_axis_group(),
        #                   self._get_y_axis_group(),
        #                   label='Axes')
        #
        # label_grp = VGroup(self._get_indicator_font_group(),
        #                    self._get_label_font_group(),
        #                    label='Fonts')
        return optgrp, display_grp  # axis_grp, label_grp

    def _get_indicator_font_group(self):
        g = VGroup(HGroup(Item('mean_indicator_fontname', label='Mean Indicator'),
                          Item('mean_indicator_fontsize', show_label=False)),
                   HGroup(Item('error_info_fontname', label='Error Info'),
                          Item('error_info_fontsize', show_label=False)),
                   show_border=True,
                   label='Info')
        return g

    def _get_mean_indicator_font(self):
        return '{} {}'.format(self.mean_indicator_fontname,
                              self.mean_indicator_fontsize)

    # def _get_fill_group(self):
    #     return self.fill_groups[0]
    #
    # def _fill_groups_default(self):
    #     return [Fill(group_id=i,
    #                  color=colornames[i + 1],
    #                  alpha=100) for i in range(10)]

    def _process_trait_change(self, name, new):
        if name in ('asymptotic_height_percent', 'use_asymptotic_limits'):
            for ap in self.aux_plots:
                ap.clear_xlimits()

        return True

    def _get_refreshable_attrs(self):
        attrs = super(IdeogramOptions, self)._get_refreshable_attrs()
        attrs.extend(['asymptotic_height_percent', 'use_asymptotic_limits'])
        return attrs

    # def _get_dump_attrs(self):
    #     attrs = super(IdeogramOptions, self)._get_dump_attrs()
    #     return attrs + [
    #         'probability_curve_kind',
    #         'mean_calculation_kind',
    #         'error_calc_method',
    #         'xlow', 'xhigh',
    #         'use_static_limits',
    #         'use_centered_range', 'centered_range',
    #         'use_asymptotic_limits', 'asymptotic_width', 'asymptotic_percent',
    #         'display_mean', 'display_mean_indicator',
    #         'x_end_caps', 'y_end_caps', 'index_attr', 'error_bar_nsigma',
    #         'analysis_number_sorting',
    #         'display_percent_error',
    #         'mean_indicator_fontname',
    #         'mean_indicator_fontsize',
    #         'mean_sig_figs',
    #         'display_inset', 'inset_location', 'inset_width', 'inset_height',
    #         # 'fill_groups',
    #         'label_fontsize',
    #         'use_cmap_analysis_number',
    #         'cmap_analysis_number',
    #         'use_latest_overlay']

    def _load_factory_defaults(self, yd):
        super(IdeogramOptions, self)._load_factory_defaults(yd)

        self._set_defaults(yd, 'calculations', ('probability_curve_kind', 'mean_calculation_kind'))
        self._set_defaults(yd, 'display', ('mean_indicator_fontsize', 'mean_sig_figs',))
        self._set_defaults(yd, 'general', ('index_attr',))

# ============= EOF =============================================
