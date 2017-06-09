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
from traits.api import Button, Int, Bool, Float, Property, on_trait_change, List, Enum, Range, Color
from traitsui.api import View, Item

from pychron.options.aux_plot import AuxPlot
from pychron.options.group.spectrum_group_options import SpectrumGroupOptions
from pychron.options.options import AgeOptions
from pychron.options.views.spectrum_views import VIEWS
from pychron.pychron_constants import NULL_STR, ERROR_TYPES, SIZES, FONTS


class SpectrumAuxPlot(AuxPlot):
    names = List([NULL_STR,
                  'Radiogenic 40Ar', 'K/Ca', 'K/Cl', 'Mol K39', 'Age Spectrum'])
    _plot_names = List(['',
                        'radiogenic_yield',
                        'kca', 'kcl', 'moles_k39', 'age_spectrum'])


class SpectrumOptions(AgeOptions):
    subview_names = List(['Main', 'Spectrum', 'Appearance', 'Plateau', 'Display', 'Groups'],
                         transient=True)
    aux_plot_klass = SpectrumAuxPlot
    edit_plateau_criteria = Button

    step_nsigma = Int(2)
    pc_nsteps = Int(3)
    pc_gas_fraction = Float(50)
    include_j_error_in_plateau = Bool(True)
    plateau_age_error_kind = Enum(*ERROR_TYPES)
    weighted_age_error_kind = Enum(*ERROR_TYPES)
    integrated_age_error_kind = Enum(*ERROR_TYPES)

    display_extract_value = Bool(False)
    display_step = Bool(False)
    display_plateau_info = Bool(True)
    display_integrated_info = Bool(True)
    display_weighted_mean_info = Bool(True)

    plateau_sig_figs = Int
    integrated_sig_figs = Int
    weighted_mean_sig_figs = Int

    plateau_font = Property
    integrated_font = Property

    plateau_fontname = Enum(*FONTS)
    plateau_fontsize = Enum(*SIZES)
    integrated_fontname = Enum(*FONTS)
    integrated_fontsize = Enum(*SIZES)
    # step_label_font_size = Enum(*SIZES)

    envelope_alpha = Range(0, 100, style='simple')
    envelope_color = Color
    user_envelope_color = Bool
    # center_line_style = Enum('No Line', 'solid', 'dash', 'dot dash', 'dot', 'long dash')
    extend_plateau_end_caps = Bool(True)
    plateau_arrow_visible = Bool
    # plateau_line_width = Float
    # plateau_line_color = Color
    # user_plateau_line_color = Bool

    plateau_method = Enum('Fleck 1977', 'Mahon 1996')
    error_calc_method = Property
    use_error_envelope_fill = Bool

    include_plateau_sample = Bool
    include_plateau_identifier = Bool

    group_options_klass = SpectrumGroupOptions

    def _get_subview(self, name):
        return VIEWS[name]

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

    def _get_plateau_font(self):
        return '{} {}'.format(self.plateau_fontname, self.plateau_fontsize)

    def _get_integrated_font(self):
        return '{} {}'.format(self.integrated_fontname, self.integrated_fontsize)
# ============= EOF =============================================
