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

from traits.api import Enum, Bool, Str, Int, Float
from traitsui.api import VGroup, HGroup, Tabbed, View, Item, UItem, Label

from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.core.persistence_options import BasePersistenceOptions
from pychron.core.pychron_traits import SingleStr
from pychron.paths import paths
from pychron.persistence_loggable import dumpable
from pychron.pychron_constants import AGE_MA_SCALARS, SIGMA


class XLSXTableWriterOptions(BasePersistenceOptions):
    table_kind = dumpable(Enum('Fusion', 'Step Heat'))

    sig_figs = dumpable(Int(6))
    j_sig_figs = dumpable(Int(6))
    subgroup_sig_figs = dumpable(Int(6))

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
    include_blanks = dumpable(Bool(True))
    include_intercepts = dumpable(Bool(True))

    use_weighted_kca = dumpable(Bool(True))
    repeat_header = dumpable(Bool(False))

    name = dumpable(Str('Untitled'))
    auto_view = dumpable(Bool(False))
    unknown_notes = dumpable(Str('''Errors quoted for individual analyses include analytical error only, without interfering reaction or J uncertainties.
Integrated age calculated by summing isotopic measurements of all steps.
Plateau age is inverse-variance-weighted mean of selected steps.
Plateau age error is inverse-variance-weighted mean error (Taylor, 1982) times root MSWD where MSWD>1.
Plateau error is weighted error of Taylor (1982).
Decay constants and isotopic abundances after {decay_ref:}
Ages calculated relative to FC-2 Fish Canyon Tuff sanidine interlaboratory standard at {monitor_age:} Ma'''))

    unknown_title = dumpable(Str('Ar/Ar analytical data.'))
    air_notes = dumpable(Str(''''''))
    air_title = dumpable(Str(''''''))
    blank_notes = dumpable(Str(''''''))
    blank_title = dumpable(Str(''''''))
    monitor_notes = dumpable(Str(''''''))
    monitor_title = dumpable(Str(''''''))

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

    plateau_nsteps = dumpable(Int(3))
    plateau_gas_fraction = dumpable(Float(50))
    fixed_step_low = dumpable(SingleStr)
    fixed_step_high = dumpable(SingleStr)

    _persistence_name = 'xlsx_table_options'

    def _table_kind_changed(self):
        if self.table_kind == 'Fusion':
            self.include_summary_percent_ar39 = False
        else:
            self.include_summary_percent_ar39 = True

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

    def traits_view(self):
        unknown_grp = VGroup(Item('unknown_title', label='Table Heading'),
                             VGroup(UItem('unknown_notes', style='custom'),
                                    show_border=True, label='Notes'), label='Unknowns')

        air_grp = VGroup(Item('air_title', label='Table Heading'),
                         VGroup(UItem('air_notes', style='custom'), show_border=True, label='Notes'), label='Airs')
        blank_grp = VGroup(Item('blank_title', label='Table Heading'),
                           VGroup(UItem('blank_notes', style='custom'), show_border=True, label='Notes'),
                           label='Blanks')
        monitor_grp = VGroup(Item('monitor_title', label='Table Heading'),
                             VGroup(UItem('monitor_notes', style='custom'), show_border=True,
                                    label='Notes'), label='Monitors')

        grp = VGroup(Item('table_kind', label='Kind'),
                     Item('name', label='Filename'),
                     Item('auto_view', label='Open in Excel'),
                     show_border=True)

        appearence_grp = VGroup(Item('hide_gridlines', label='Hide Gridlines'),
                                Item('power_units', label='Power Units'),

                                Item('age_units', label='Age Units'),
                                Item('repeat_header', label='Repeat Header'),

                                show_border=True, label='Appearance')

        sig_figs_grp = VGroup(Item('sig_figs', label='Default'),
                              Item('subgroup_sig_figs', label='Subgroup'),
                              Item('j_sig_figs', label='Flux'),
                              Item('summary_sig_figs', label='Summary'),
                              Item('ensure_trailing_zeros', label='Ensure Trailing Zeros'),
                              show_border=True, label='Significant Figures')

        arar_col_grp = VGroup(Item('include_F', label='40Ar*/39ArK'),
                              Item('include_radiogenic_yield', label='%40Ar*'),
                              Item('include_kca', label='K/Ca'),
                              Item('use_weighted_kca', label='K/Ca Weighted Mean', enabled_when='include_kca'),
                              Item('include_k2o', label='K2O wt. %'),
                              Item('include_production_ratios', label='Production Ratios'),
                              Item('include_plateau_age', label='Plateau',
                                   visible_when='table_kind=="Step Heat"'),
                              Item('include_integrated_age', label='Integrated',
                                   visible_when='table_kind=="Step Heat"'),
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
        g1 = VGroup(grp, columns_grp, appearence_grp, sig_figs_grp, label='Main')

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
# ============= EOF =============================================
