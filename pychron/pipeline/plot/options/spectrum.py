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
from traits.api import Int, Property, Bool, Enum, Float, Color, Range, Button, on_trait_change
from traitsui.api import View, Item, Group, HGroup, UItem, EnumEditor, spring, VGroup

# ============= standard library imports ========================
import re
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor

# from pychron.pipeline.plot.options import AgeOptions
from pychron.pipeline.plot.options.age import AgeOptions
from pychron.pipeline.plot.options.base import dumpable
# from pychron.pipeline.plot.options import SIZES
# from pychron.pipeline.plot.options import SpectrumGroupOptions, SpectrumGroupEditor
from pychron.pipeline.plot.options.figure_plotter_options import SIZES
from pychron.pipeline.plot.options.option import SpectrumPlotOptions
from pychron.pipeline.plot.options.spectrum_group_options import SpectrumGroupEditor, SpectrumGroupOptions
from pychron.pychron_constants import ERROR_TYPES

plat_regex = re.compile(r'\w{1,2}-{1}\w{1,2}$')


class SpectrumOptions(AgeOptions):
    label = 'Spectrum'
    aux_plot_name = 'Age'
    aux_plot_klass = SpectrumPlotOptions
    edit_plateau_criteria = Button

    step_nsigma = dumpable(Int, 2)
    pc_nsteps = dumpable(Int, 3)
    pc_gas_fraction = dumpable(Float, 50)
    include_j_error_in_plateau = dumpable(Bool, True)
    plateau_age_error_kind = dumpable(Enum, *ERROR_TYPES)

    display_extract_value = dumpable(Bool, False)
    display_step = dumpable(Bool, False)
    display_plateau_info = dumpable(Bool, True)
    display_integrated_info = dumpable(Bool, True)
    plateau_sig_figs = dumpable(Int)
    integrated_sig_figs = dumpable(Int)

    plateau_font_size = dumpable(Enum, *SIZES)
    integrated_font_size = dumpable(Enum, *SIZES)
    step_label_font_size = dumpable(Enum, *SIZES)
    envelope_alpha = dumpable(Range, 0, 100, style='simple')
    envelope_color = dumpable(Color)
    user_envelope_color = dumpable(Bool)
    center_line_style = dumpable(Enum, 'No Line', 'solid', 'dash', 'dot dash', 'dot', 'long dash')
    extend_plateau_end_caps = dumpable(Bool, True)
    plateau_arrow_visible = dumpable(Bool)
    # plateau_line_width = Float
    # plateau_line_color = Color
    # user_plateau_line_color = Bool

    plateau_method = dumpable(Enum, 'Fleck 1977', 'Mahon 1996')
    error_calc_method = Property
    use_error_envelope_fill = dumpable(Bool)

    include_plateau_sample = dumpable(Bool)
    include_plateau_identifier = dumpable(Bool)

    # edit_groups_button = Button
    group_editor_klass = SpectrumGroupEditor
    options_klass = SpectrumGroupOptions

    # handlers
    @on_trait_change('display_step,display_extract_value')
    def _handle_labels(self):
        labels_enabled = self.display_extract_value or self.display_step
        self.aux_plots[-1].show_labels = labels_enabled

    #
    # def _edit_groups_button_fired(self):
    #     eg = SpectrumGroupEditor(error_envelopes=self.groups)
    #     info = eg.edit_traits()
    #     if info.result:
    #         self.refresh_plot_needed = True

    def _edit_plateau_criteria_fired(self):
        v = View(Item('pc_nsteps', label='Num. Steps', tooltip='Number of contiguous steps'),
                 Item('pc_gas_fraction', label='Min. Gas%',
                      tooltip='Plateau must represent at least Min. Gas% release'),
                 buttons=['OK', 'Cancel'],
                 title='Edit Plateau Criteria',
                 kind='livemodal')
        self.edit_traits(v)

    def _get_error_calc_method(self):
        return self.plateau_age_error_kind

    def _set_error_calc_method(self, v):
        self.plateau_age_error_kind = v

    # def _get_info_group(self):
    # g = VGroup(
    # HGroup(Item('show_info', label='Display Info'),
    # Item('show_mean_info', label='Mean', enabled_when='show_info'),
    # Item('show_error_type_info', label='Error Type', enabled_when='show_info')
    # ),
    # HGroup(Item('display_step'), Item('display_extract_value'),
    # Item('display_plateau_info')),
    # show_border=True, label='Info')

    # return g

    # def _get_plateau_steps(self):
    # return self._plateau_steps
    #
    # def _set_plateau_steps(self, v):
    # if v:
    # self._plateau_steps = v
    #
    # def _validate_plateau_steps(self, v):
    # if plat_regex.match(v):
    # s, e = v.split('-')
    # try:
    # assert s < e
    #             return v
    #         except AssertionError:
    #             pass

    # def _get_dump_attrs(self):
    #     attrs = super(SpectrumOptions, self)._get_dump_attrs()
    #     return attrs + ['step_nsigma',
    #                     # 'calculate_fixed_plateau',
    #                     # 'calculate_fixed_plateau_start',
    #                     # 'calculate_fixed_plateau_end',
    #                     'display_extract_value',
    #                     'display_step',
    #                     'display_plateau_info',
    #                     'display_integrated_info',
    #                     'plateau_font_size',
    #                     'integrated_font_size',
    #                     'step_label_font_size',
    #                     # 'envelope_alpha',
    #                     # 'user_envelope_color', 'envelope_color',
    #                     # 'groups',
    #                     # '_plateau_steps',
    #                     'center_line_style',
    #                     'extend_plateau_end_caps',
    #                     # 'plateau_line_width',
    #                     # 'plateau_line_color',
    #                     # 'user_plateau_line_color',
    #                     'include_j_error_in_plateau',
    #                     'plateau_age_error_kind',
    #                     'plateau_sig_figs',
    #                     'integrated_sig_figs',
    #                     'use_error_envelope_fill',
    #                     'plateau_method',
    #                     'pc_nsteps',
    #                     'pc_gas_fraction',
    #                     'legend_location',
    #                     'include_legend',
    #                     'include_sample_in_legend']

    def _get_groups(self):
        lgrp = VGroup(Item('plateau_method', label='Method'),
                      Item('nsigma'),
                      Item('plateau_age_error_kind',
                           width=-100,
                           label='Error Type'),
                      Item('include_j_error_in_plateau', label='Include J Error'))
        rgrp = VGroup(Item('center_line_style',
                           label='Line Stype'),
                      Item('extend_plateau_end_caps',
                           label='Extend End Caps'),
                      icon_button_editor('edit_plateau_criteria', 'cog',
                                         tooltip='Edit Plateau Criteria'), )
        plat_grp = HGroup(lgrp, rgrp)

        # grp_grp = VGroup(UItem('group',
        #                        style='custom',
        #                        editor=InstanceEditor(view='simple_view')),
        #                  show_border=True,
        #                  label='Group Attributes')

        error_grp = VGroup(HGroup(Item('step_nsigma',
                                       editor=EnumEditor(values=[1, 2, 3]),
                                       tooltip='Set the size of the error envelope in standard deviations',
                                       label='N. Sigma')),
                           show_border=True,
                           label='Error Envelope')

        display_grp = Group(HGroup(UItem('show_info',
                                         tooltip='Show general info in the upper right corner'),
                                   show_border=True,
                                   label='General'),
                            VGroup(Item('include_legend', label='Show'),
                                   Item('include_sample_in_legend', label='Include Sample'),
                                   Item('legend_location', label='Location'),
                                   label='Legend', show_border=True),

                            HGroup(Item('display_step', label='Step'),
                                   Item('display_extract_value', label='Power/Temp'),
                                   spring,
                                   Item('step_label_font_size', label='Size'),
                                   show_border=True,
                                   label='Labels'),
                            VGroup(HGroup(UItem('display_plateau_info',
                                                tooltip='Display plateau info'),
                                          Item('plateau_font_size', label='Size',
                                               enabled_when='display_plateau_info'),
                                          Item('plateau_sig_figs', label='SigFigs')),
                                   HGroup(Item('include_plateau_sample',
                                               tooltip='Add the Sample name to the Plateau indicator',
                                               label='Sample'),
                                          Item('include_plateau_identifier',
                                               tooltip='Add the Identifier to the Plateau indicator',
                                               label='Identifier')),
                                   Item('plateau_arrow_visible'),
                                   show_border=True,
                                   label='Plateau'),
                            HGroup(UItem('display_integrated_info',
                                         tooltip='Display integrated age info'),
                                   Item('integrated_font_size', label='Size',
                                        enabled_when='display_integrated_info'),
                                   Item('integrated_sig_figs', label='SigFigs'),
                                   show_border=True,
                                   label='Integrated'),
                            show_border=True,
                            label='Display')
        plat_grp = VGroup(plat_grp, error_grp,
                          label='Plateau')
        return plat_grp, display_grp
        # g = Group(
        #     self._get_title_group(),
        #     grp_grp,
        #     plat_grp,
        #     error_grp,
        #     display_grp,
        # self._get_info_group(),
        # label='Options')

        # label_grp = VGroup(self._get_x_axis_group(),
        #                    self._get_y_axis_group(),
        #                    label='Fonts')
        # return g,

    def _load_factory_defaults(self, yd):
        super(SpectrumOptions, self)._load_factory_defaults(yd)

        self._set_defaults(yd, 'legend', ('legend_location',
                                          'include_legend',
                                          'include_sample_in_legend'))

        self._set_defaults(yd, 'plateau', ('plateau_line_width',
                                           'plateau_line_color',
                                           'plateau_font_size',
                                           'plateau_sig_figs',
                                           # 'calculate_fixed_plateau',
                                           # 'calculate_fixed_plateau_start',
                                           # 'calculate_fixed_plateau_end',
                                           'pc_nsteps',
                                           'pc_gas_fraction'))

        self._set_defaults(yd, 'integrated', ('integrated_font_size',
                                              'integrated_sig_figs',))
        self._set_defaults(yd, 'labels', ('display_step',
                                          'display_extract_value',
                                          'step_label_font_size'))

        # ============= EOF =============================================
        # HGroup(UItem('error_envelope',
        #              style='custom',
        #              editor=InstanceEditor(view='simple_view')),
        #        icon_button_editor('edit_envelopes_button', 'cog')),
        # HGroup(UItem('user_envelope_color'),
        #        Item('envelope_color',
        #             label='Color',
        #             enabled_when='user_envelope_color'),
        #        Item('envelope_alpha',
        #             label='Opacity',
        #             enabled_when='use_error_envelope_fill',
        #             tooltip='Set the opacity (alpha-value) for the error envelope')),

        # plat_grp = Group(
        #     HGroup(Item('plateau_method', label='Method'),
        #            icon_button_editor('edit_plateau_criteria', 'cog',
        #                               tooltip='Edit Plateau Criteria')),
        #     Item('center_line_style'),
        #     Item('extend_plateau_end_caps'),
        #     # Item('plateau_line_width'),
        #     # HGroup(UItem('user_plateau_line_color'),
        #     #        Item('plateau_line_color', enabled_when='user_plateau_line_color')),
        #
        #     Item('nsigma'),
        #     Item('plateau_age_error_kind',
        #          width=-100,
        #          label='Error Type'),
        #     Item('include_j_error_in_plateau', label='Include J Error'),
        #     # HGroup(
        #     #     Item('calculate_fixed_plateau',
        #     #          label='Calc. Plateau',
        #     #          tooltip='Calculate a plateau over provided steps'),
        #     #     Item('calculate_fixed_plateau_start', label='Start'),
        #     #     Item('calculate_fixed_plateau_end', label='End')
        #     # ),
        #     show_border=True,
        #     label='Plateau')

        # error_grp = VGroup(HGroup(Item('step_nsigma',
        #                                editor=EnumEditor(values=[1, 2, 3]),
        #                                tooltip='Set the size of the error envelope in standard deviations',
        #                                label='N. Sigma'),
        #                           Item('use_error_envelope_fill', label='Fill')),
        #                    HGroup(UItem('user_envelope_color'),
        #                           Item('envelope_color',
        #                                label='Color',
        #                                enabled_when='user_envelope_color'),
        #                           Item('envelope_alpha',
        #                                label='Opacity',
        #                                enabled_when='use_error_envelope_fill',
        #                                tooltip='Set the opacity (alpha-value) for the error envelope')),
        #                    show_border=True,
        #                    label='Error Envelope')
        # grp_grp = VGroup(HGroup(UItem('group',
        #                               style='custom',
        #                               editor=InstanceEditor(view='simple_view')),
        #                         icon_button_editor('edit_groups_button', 'cog')),
        #                  show_border=True,
        #                  label='Group Attributes')
