# ===============================================================================
# Copyright 2018 ross
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


import os

import yaml
from traits.api import Enum, Bool, Str, Int, Float, Color, List
from traitsui.api import VGroup, HGroup, Tabbed, View, Item, UItem, Label, EnumEditor

from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.core.persistence_options import BasePersistenceOptions
from pychron.core.pychron_traits import SingleStr
from pychron.paths import paths
from pychron.persistence_loggable import dumpable
from pychron.pychron_constants import AGE_MA_SCALARS, SIGMA, AGE_SORT_KEYS


class XLSXAnalysisTableWriterOptions(BasePersistenceOptions):
    sig_figs = dumpable(Int(6))
    j_sig_figs = dumpable(Int(6))
    ic_sig_figs = dumpable(Int(6))
    disc_sig_figs = dumpable(Int(6))

    age_sig_figs = dumpable(Int(6))
    summary_age_sig_figs = dumpable(Int(6))

    kca_sig_figs = dumpable(Int(6))
    summary_kca_sig_figs = dumpable(Int(6))

    rad40_percent_sig_figs = dumpable(Int(6))
    cumulative_ar39_sig_figs = dumpable(Int(6))

    signal_sig_figs = dumpable(Int(6))
    j_sig_figs = dumpable(Int(6))
    ic_sig_figs = dumpable(Int(6))
    disc_sig_figs = dumpable(Int(6))
    decay_sig_figs = dumpable(Int(6))
    correction_sig_figs = dumpable(Int(6))
    sens_sig_figs = dumpable(Int(2))
    k2o_sig_figs = dumpable(Int(3))

    ensure_trailing_zeros = dumpable(Bool(False))

    power_units = dumpable(Enum('W', 'C'))
    age_units = dumpable(Enum('Ma', 'Ga', 'ka', 'a'))
    hide_gridlines = dumpable(Bool(False))
    include_F = dumpable(Bool(True))
    include_radiogenic_yield = dumpable(Bool(True))
    include_production_ratios = dumpable(Bool(True))
    include_plateau_age = dumpable(Bool(True))
    include_integrated_age = dumpable(Bool(True))
    include_isochron_age = dumpable(Bool(True))
    include_kca = dumpable(Bool(True))
    include_rundate = dumpable(Bool(True))
    include_time_delta = dumpable(Bool(True))
    include_k2o = dumpable(Bool(True))
    include_isochron_ratios = dumpable(Bool(False))
    include_sensitivity = dumpable(Bool(True))
    sensitivity_units = dumpable(Str('mol/fA'))

    include_blanks = dumpable(Bool(True))
    include_intercepts = dumpable(Bool(True))
    include_percent_ar39 = dumpable(Bool(True))
    # use_weighted_kca = dumpable(Bool(True))
    # kca_error_kind = dumpable(Enum(*ERROR_TYPES))
    repeat_header = dumpable(Bool(False))
    highlight_non_plateau = Bool(True)
    highlight_color = dumpable(Color)

    name = dumpable(Str('Untitled'))
    auto_view = dumpable(Bool(False))

    unknown_note_name = dumpable(Str('Default'))
    available_unknown_note_names = List

    unknown_notes = dumpable(Str('''Errors quoted for individual analyses include analytical error only, without interfering reaction or J uncertainties.
Integrated age calculated by summing isotopic measurements of all steps.
Plateau age is inverse-variance-weighted mean of selected steps.
Plateau age error is inverse-variance-weighted mean error (Taylor, 1982) times root MSWD where MSWD>1.
Plateau error is weighted error of Taylor (1982).
Decay constants and isotopic abundances after {decay_ref:}
Ages calculated relative to FC-2 Fish Canyon Tuff sanidine interlaboratory standard at {monitor_age:} Ma'''))

    unknown_corrected_note = dumpable(Str('''Corrected: Isotopic intensities corrected for blank, baseline, 
    radioactivity decay and detector intercalibration, not for interfering reactions.'''))
    unknown_intercept_note = dumpable(Str('''Intercepts: t-zero intercept corrected for detector baseline.'''))
    unknown_time_note = dumpable(Str('''Time interval (days) between end of irradiation and beginning of analysis.'''))

    unknown_x_note = dumpable(Str('''X symbol preceding sample ID denotes analyses 
    excluded from weighted-mean age calculations.'''))
    unknown_px_note = dumpable(Str('''pX symbol preceding sample ID denotes analyses
    excluded plateau age calculations.'''))

    unknown_title = dumpable(Str('Ar/Ar analytical data.'))
    air_notes = dumpable(Str(''))
    air_title = dumpable(Str(''))
    blank_notes = dumpable(Str(''))
    blank_title = dumpable(Str(''))
    monitor_notes = dumpable(Str(''))
    monitor_title = dumpable(Str(''))
    summary_notes = dumpable(Str(''))

    include_summary_sheet = dumpable(Bool(True))
    include_summary_age = dumpable(Bool(True))
    include_summary_age_type = dumpable(Bool(True))
    include_summary_material = dumpable(Bool(True))
    include_summary_sample = dumpable(Bool(True))

    include_summary_identifier = dumpable(Bool(True))
    include_summary_unit = dumpable(Bool(True))
    include_summary_location = dumpable(Bool(True))
    include_summary_irradiation = dumpable(Bool(True))
    include_summary_n = dumpable(Bool(True))
    include_summary_percent_ar39 = dumpable(Bool(True))
    include_summary_mswd = dumpable(Bool(True))
    include_summary_kca = dumpable(Bool(True))
    include_summary_comments = dumpable(Bool(True))

    summary_age_nsigma = dumpable(Enum(1, 2, 3))
    summary_kca_nsigma = dumpable(Enum(1, 2, 3))

    asummary_kca_nsigma = dumpable(Enum(1, 2, 3))
    asummary_age_nsigma = dumpable(Enum(1, 2, 3))

    plateau_nsteps = dumpable(Int(3))
    plateau_gas_fraction = dumpable(Float(50))
    fixed_step_low = dumpable(SingleStr)
    fixed_step_high = dumpable(SingleStr)

    group_age_sorting = dumpable(Enum(*AGE_SORT_KEYS))
    subgroup_age_sorting = dumpable(Enum(*AGE_SORT_KEYS))
    individual_age_sorting = dumpable(Enum(*AGE_SORT_KEYS))

    _persistence_name = 'xlsx_table_options'

    def __init__(self, *args, **kw):
        super(XLSXAnalysisTableWriterOptions, self).__init__(*args, **kw)
        # self.load_notes()
        # self._load_note_names()

        self._load_notes()
        self._unknown_note_name_changed(self.unknown_note_name)

    def _load_notes(self):
        p = os.path.join(paths.user_pipeline_dir, 'table_notes.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as rf:
                obj = yaml.load(rf)

                setattr(self, 'summary_notes', obj.get('summary_notes', ''))

                for grpname in ('unknown',):
                    grp = obj.get('{}_notes'.format(grpname))
                    if grp:
                        try:
                            setattr(self, 'available_{}_note_names'.format(grpname), list(grp.keys()))
                        except AttributeError:
                            pass

    def _unknown_note_name_changed(self, new):
        grp = self._load_note('unknown_notes')
        if grp is not None:
            sgrp = grp.get(new)
            if sgrp:
                self.unknown_notes = sgrp.get('main', '')
                for k in ('corrected', 'x', 'px', 'intercept', 'time'):
                    v = sgrp.get(k)
                    if v is not None:
                        setattr(self, 'unknown_{}_note'.format(k), v)

    def _load_note(self, group):
        p = os.path.join(paths.user_pipeline_dir, 'table_notes.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as rf:
                obj = yaml.load(rf)
                return obj.get(group)

    @property
    def age_scalar(self):
        return AGE_MA_SCALARS[self.age_units]

    @property
    def path(self):
        name = self.name
        if not name or name == 'Untitled':
            path, _ = unique_path2(paths.table_dir, 'Untitled', extension='.xlsx')
        else:
            path = os.path.join(paths.table_dir, add_extension(name, ext='.xlsx'))
        return path

    # def load_notes(self):
    #     p = os.path.join(paths.user_pipeline_dir, 'table_notes.yaml')
    #     if os.path.isfile(p):
    #         with open(p, 'r') as rf:
    #             obj = yaml.load(rf)
    #             for k, v in obj.items():
    #                 if k == 'summary_notes':
    #                     setattr(self, 'summary_notes', v)

    def traits_view(self):
        unknown_grp = VGroup(Item('unknown_title', label='Table Heading', springy=True),
                             VGroup(VGroup(UItem('unknown_note_name',
                                                 editor=EnumEditor(name='available_unknown_note_names')),
                                           UItem('unknown_notes', style='custom'), label='Main', show_border=True),
                                    VGroup(UItem('unknown_corrected_note', height=-50, style='custom'),
                                           label='Corrected', show_border=True),
                                    VGroup(UItem('unknown_intercept_note', height=-50, style='custom'),
                                           label='Intercept', show_border=True),
                                    VGroup(UItem('unknown_time_note', height=-50, style='custom'), label='Time',
                                           show_border=True),
                                    VGroup(UItem('unknown_x_note', height=-50, style='custom'), label='X',
                                           show_border=True),
                                    VGroup(UItem('unknown_px_note', height=-50, style='custom'), label='pX',
                                           show_border=True),
                                    show_border=True, label='Notes'), label='Unknowns')

        air_grp = VGroup(Item('air_title', label='Table Heading'),
                         VGroup(UItem('air_notes', style='custom'), show_border=True, label='Notes'), label='Airs')
        blank_grp = VGroup(Item('blank_title', label='Table Heading'),
                           VGroup(UItem('blank_notes', style='custom'), show_border=True, label='Notes'),
                           label='Blanks')
        monitor_grp = VGroup(Item('monitor_title', label='Table Heading'),
                             VGroup(UItem('monitor_notes', style='custom'), show_border=True,
                                    label='Notes'), label='Monitors')

        grp = VGroup(Item('name', label='Filename'),
                     Item('auto_view', label='Open in Excel'),
                     show_border=True)

        appearence_grp = VGroup(Item('hide_gridlines', label='Hide Gridlines'),
                                Item('power_units', label='Power Units'),
                                Item('age_units', label='Age Units'),
                                Item('sensitivity_units', label='Sensitivity Units'),
                                Item('group_age_sorting', label='Group Age Sorting'),
                                Item('subgroup_age_sorting', label='SubGroup Age Sorting'),
                                Item('individual_age_sorting', label='Individual Age Sorting'),
                                Item('asummary_kca_nsigma', label='K/Ca Nsigma'),
                                Item('asummary_age_nsigma', label='Age Nsigma'),
                                Item('repeat_header', label='Repeat Header'),
                                HGroup(Item('highlight_non_plateau'),
                                       UItem('highlight_color', enabled_when='highlight_non_plateau')),
                                show_border=True, label='Appearance')

        sig_figs_grp = VGroup(Item('sig_figs', label='Default'),

                              Item('age_sig_figs', label='Age'),
                              Item('summary_age_sig_figs', label='Summary Age'),

                              Item('kca_sig_figs', label='K/Ca'),
                              Item('summary_kca_sig_figs', label='Summary K/Ca'),

                              Item('rad40_percent_sig_figs', label='%40Ar*'),
                              Item('cumulative_ar39_sig_figs', label='Cum. %39Ar'),

                              Item('signal_sig_figs', label='Signal'),
                              Item('j_sig_figs', label='Flux'),
                              Item('ic_sig_figs', label='IC'),
                              Item('disc_sig_figs', label='Disc.'),
                              Item('decay_sig_figs', label='Decay'),
                              Item('correction_sig_figs', label='Correction Factors'),
                              Item('sens_sig_figs', label='Sensitivity'),
                              Item('k2o_sig_figs', label='K2O'),
                              # Item('subgroup_sig_figs', label='Subgroup'),
                              # Item('j_sig_figs', label='Flux'),
                              # Item('summary_sig_figs', label='Summary'),
                              # Item('ic_sig_figs', label='IC'),
                              # Item('disc_sig_figs', label='Disc.'),

                              Item('ensure_trailing_zeros', label='Ensure Trailing Zeros'),
                              show_border=True, label='Significant Figures')

        arar_col_grp = VGroup(Item('include_F', label='40Ar*/39ArK'),
                              Item('include_percent_ar39', label='Cumulative %39Ar'),
                              Item('include_radiogenic_yield', label='%40Ar*'),
                              Item('include_kca', label='K/Ca'),
                              # Item('use_weighted_kca', label='K/Ca Weighted Mean'),
                              # Item('kca_error_kind', label='K/Ca Error'),
                              Item('include_sensitivity', label='Sensitivity'),
                              Item('include_k2o', label='K2O wt. %'),
                              Item('include_production_ratios', label='Production Ratios'),
                              Item('include_plateau_age', label='Plateau'),
                              Item('include_integrated_age', label='Integrated'),
                              Item('include_isochron_age', label='Isochron'),
                              Item('include_isochron_ratios', label='Isochron Ratios'),
                              Item('include_time_delta', label='Time since Irradiation'),
                              label='Ar/Ar')

        general_col_grp = VGroup(Item('include_rundate', label='Analysis RunDate'),
                                 Item('include_blanks', label='Applied Blank'),
                                 Item('include_intercepts', label='Intercepts'),
                                 label='General')
        columns_grp = HGroup(general_col_grp, arar_col_grp,
                             label='Columns', show_border=True)

        g1 = VGroup(HGroup(grp, appearence_grp),
                    HGroup(columns_grp, sig_figs_grp), label='Main')

        summary_grp = VGroup(Item('include_summary_sheet', label='Summary Sheet'),
                             VGroup(

                                 Item('include_summary_sample', label='Sample'),
                                 Item('include_summary_identifier', label='Identifier'),
                                 Item('include_summary_unit', label='Unit'),
                                 Item('include_summary_location', label='Location'),
                                 Item('include_summary_material', label='Material'),
                                 Item('include_summary_irradiation', label='Irradiation'),
                                 Item('include_summary_age_type', label='Age Type'),
                                 Item('include_summary_n', label='N'),
                                 Item('include_summary_percent_ar39', label='%39Ar'),
                                 Item('include_summary_mswd', label='MSWD'),
                                 HGroup(Item('include_summary_kca', label='KCA'),
                                        Item('summary_kca_nsigma', label=SIGMA)),
                                 HGroup(Item('include_summary_age', label='Age'),
                                        Item('summary_age_nsigma', label=SIGMA)),
                                 Item('include_summary_comments', label='Comments'),
                                 enabled_when='include_summary_sheet',
                                 label='Columns',
                                 show_border=True),
                             VGroup(UItem('summary_notes', style='custom'), show_border=True, label='Notes'),
                             label='Summary')

        plat_grp = VGroup(Item('plateau_nsteps', label='Num. Steps', tooltip='Number of contiguous steps'),
                          Item('plateau_gas_fraction', label='Min. Gas%',
                               tooltip='Plateau must represent at least Min. Gas% release'),
                          HGroup(UItem('fixed_step_low'),
                                 Label('To'),
                                 UItem('fixed_step_high'),
                                 show_border=True,
                                 label='Fixed Steps'),
                          visible_when='table_kind=="Step Heat"',
                          show_border=True,
                          label='Plateau')

        calc_grp = VGroup(plat_grp, label='Calc.')

        v = View(Tabbed(g1, unknown_grp, calc_grp, blank_grp, air_grp, monitor_grp, summary_grp),
                 resizable=True,
                 width=750,
                 title='XLSX Analysis Table Options',
                 buttons=['OK', 'Cancel'])
        return v


if __name__ == '__main__':
    # from pychron.paths import paths
    paths.build('~/PychronDev')
    e = XLSXAnalysisTableWriterOptions()
    e.configure_traits()
# ============= EOF =============================================
