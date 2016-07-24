# ===============================================================================
# Copyright 2016 ross
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
import re
import subprocess

import xlsxwriter
from traits.api import Instance, Enum, Str, Bool
from traitsui.api import View, VGroup, Item
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.filetools import add_extension, unique_path2
from pychron.core.persistence_options import BasePersistenceOptions
from pychron.paths import paths
from pychron.persistence_loggable import dumpable
from pychron.pipeline.tables.base_table_writer import BaseTableWriter
from pychron.pipeline.tables.util import iso_value, value, error, icf_value, icf_error, correction_value
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA

subreg = re.compile(r'^<sub>(?P<item>\w+)</sub>')
supreg = re.compile(r'^<sup>(?P<item>\w+)</sup>')


class XLSXTableWriterOptions(BasePersistenceOptions):
    power_units = dumpable(Enum('W', 'C'))
    age_units = dumpable(Enum('Ma', 'Ga', 'ka', 'a'))
    hide_gridlines = dumpable(Bool(False))
    include_F = dumpable(Bool(True))
    include_radiogenic_yield = dumpable(Bool(True))
    include_production_ratios = dumpable(Bool(True))
    include_plateau_age = dumpable(Bool(True))
    include_integrated_age = dumpable(Bool(True))
    include_isochron_age = dumpable(Bool(True))
    _persistence_name = 'xlsx_table_options'
    name = Str('Untitled')
    title = 'Table. X'

    @property
    def path(self):
        name = self.name
        if not name or name == 'Untitled':
            path = unique_path2(paths.table_dir, 'Untitled', extension='.xlsx')
        else:
            path = os.path.join(paths.table_dir, add_extension(name, ext='.xlsx'))
        return path

    def traits_view(self):
        v = View(Item('name', label='Filename'),
                 # Item('title', label='Table Title'),
                 Item('power_units', label='Power Units'),
                 Item('age_units', label='Age Units'),
                 Item('hide_gridlines', label='Hide Gridlines'),
                 Item('include_F', label='Include 40Ar*/39ArK'),
                 Item('include_radiogenic_yield', label='Include %40Ar*'),
                 Item('include_production_ratios', label='Include Production Ratios'),
                 VGroup(
                     Item('include_plateau_age', label='Include Plateau'),
                     Item('include_integrated_age', label='Include Integrated'),
                     Item('include_isochron_age', label='Include Isochron'), label='Ages', show_border=True),
                 title='XLSX Analysis Table Options',
                 buttons=['OK', 'Cancel'])
        return v


class XLSXTableWriter(BaseTableWriter):
    _workbook = None
    _current_row = 0
    _bold = None

    _options = Instance(XLSXTableWriterOptions)

    def _get_columns(self, name):
        options = self._options

        ubit = name in ('Unknowns', 'Monitor')
        age_units = '({})'.format(options.age_units)
        columns = [(True, 'Status', '', 'status'),
                   (True, 'N', '', 'aliquot_step_str'),
                   (ubit, 'Power', options.power_units, 'extract_value'),
                   (ubit, 'K/Ca', '', 'kca', value),
                   (ubit, PLUSMINUS_ONE_SIGMA, '', 'kca', error),
                   (ubit, 'Age', age_units, 'age', value),
                   (ubit, PLUSMINUS_ONE_SIGMA, age_units, 'age_err_wo_j', value),
                   (ubit and options.include_radiogenic_yield,
                    ('%', '<sup>40</sup>', 'Ar'), '(%)', 'rad40_percent', value),
                   (ubit and options.include_F,
                    ('<sup>40</sup>', 'Ar*/', '<sup>39</sup>', 'Ar', '<sub>K</sub>'), '', 'uF', value),

                   # True, disc/ic corrected
                   (True, ('<sup>40</sup>', 'Ar'), '(fA)', 'Ar40', iso_value('disc_ic_corrected')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar40', iso_value('disc_ic_corrected', ve='error')),
                   (True, ('<sup>39</sup>', 'Ar'), '(fA)', 'Ar39', iso_value('disc_ic_corrected')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar39', iso_value('disc_ic_corrected', ve='error')),
                   (True, ('<sup>38</sup>', 'Ar'), '(fA)', 'Ar38', iso_value('disc_ic_corrected')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar38', iso_value('disc_ic_corrected', ve='error')),
                   (True, ('<sup>37</sup>', 'Ar'), '(fA)', 'Ar37', iso_value('disc_ic_corrected')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar37', iso_value('disc_ic_corrected', ve='error')),
                   (True, ('<sup>36</sup>', 'Ar'), '(fA)', 'Ar36', iso_value('disc_ic_corrected')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar36', iso_value('disc_ic_corrected', ve='error')),

                   # intercepts baseline corrected
                   (True, ('<sup>40</sup>', 'Ar'), '(fA)', 'Ar40', iso_value('intercept')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar40', iso_value('intercept', ve='error')),
                   (True, ('<sup>39</sup>', 'Ar'), '(fA)', 'Ar39', iso_value('intercept')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar39', iso_value('intercept', ve='error')),
                   (True, ('<sup>38</sup>', 'Ar'), '(fA)', 'Ar38', iso_value('intercept')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar38', iso_value('intercept', ve='error')),
                   (True, ('<sup>37</sup>', 'Ar'), '(fA)', 'Ar37', iso_value('intercept')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar37', iso_value('intercept', ve='error')),
                   (True, ('<sup>36</sup>', 'Ar'), '(fA)', 'Ar36', iso_value('intercept')),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'Ar36', iso_value('intercept', ve='error')),

                   # blanks
                   (ubit, ('<sup>40</sup>', 'Ar'), '(fA)', 'Ar40', iso_value('blank')),
                   (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ar40', iso_value('blank', ve='error')),
                   (ubit, ('<sup>39</sup>', 'Ar'), '(fA)', 'Ar39', iso_value('blank')),
                   (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ar39', iso_value('blank', ve='error')),
                   (ubit, ('<sup>38</sup>', 'Ar'), '(fA)', 'Ar38', iso_value('blank')),
                   (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ar38', iso_value('blank', ve='error')),
                   (ubit, ('<sup>37</sup>', 'Ar'), '(fA)', 'Ar37', iso_value('blank')),
                   (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ar37', iso_value('blank', ve='error')),
                   (ubit, ('<sup>36</sup>', 'Ar'), '(fA)', 'Ar36', iso_value('blank')),
                   (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ar36', iso_value('blank', ve='error')),

                   (True, 'Disc', '', 'discrimination', value),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'discrimination', error),
                   (True, ('IC', '<sup>CDD</sup>'), '', 'CDD_ic_factor', icf_value),
                   (True, PLUSMINUS_ONE_SIGMA, '', 'CDD_ic_factor', icf_error),

                   (ubit, 'J', '', 'j', value),
                   (ubit, PLUSMINUS_ONE_SIGMA, '', 'j', error),
                   (ubit, ('<sup>39</sup>', 'Ar Decay'), '', 'ar39decayfactor', value),
                   (ubit, ('<sup>37</sup>', 'Ar Decay'), '', 'ar37decayfactor', value),
                   (ubit, ('(', '<sup>40</sup>', 'Ar/', '<sup>39</sup>', 'Ar)', '<sub>K</sub>'), '', 'K4039',
                    correction_value())]

        if options.include_production_ratios:
            pr = [(ubit, PLUSMINUS_ONE_SIGMA, '', 'K4039', correction_value(ve='error')),
                  (ubit, ('(', '<sup>38</sup>', 'Ar/', '<sup>39</sup>', 'Ar)', '<sub>K</sub>'), '', 'K3839',
                   correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'K3839', correction_value(ve='error')),
                  (ubit, ('(', '<sup>37</sup>', 'Ar/', '<sup>39</sup>', 'Ar)', '<sub>K</sub>'), '', 'K3739',
                   correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'K3739', correction_value(ve='error')),
                  (ubit, ('(', '<sup>39</sup>', 'Ar/', '<sup>37</sup>', 'Ar)', '<sub>Ca</sub>'), '', 'Ca3937',
                   correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ca3937', correction_value(ve='error')),
                  (ubit, ('(', '<sup>38</sup>', 'Ar/', '<sup>37</sup>', 'Ar)', '<sub>Ca</sub>'), '', 'Ca3837',
                   correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ca3837', correction_value(ve='error')),
                  (ubit, ('(', '<sup>36</sup>', 'Ar/', '<sup>37</sup>', 'Ar)', '<sub>Ca</sub>'), '', 'Ca3637',
                   correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ca3637', correction_value(ve='error')),
                  (ubit, ('(', '<sup>36</sup>', 'Ar/', '<sup>38</sup>', 'Ar)', '<sub>Cl</sub>'), '', 'Cl3638',
                   correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'Cl3638', correction_value(ve='error')),
                  (ubit, 'Ca/K', '', 'Ca_K', correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'Ca_K', correction_value(ve='error')),
                  (ubit, 'Cl/K ', '', 'Cl_K', correction_value()),
                  (ubit, PLUSMINUS_ONE_SIGMA, '', 'Cl_K', correction_value(ve='error'))]
            columns.extend(pr)

        return [c for c in columns if c[0]]

    def build(self, unknowns=None, airs=None, blanks=None, monitors=None, options=None):
        if options is None:
            options = XLSXTableWriterOptions()

        self._options = options

        path = options.path
        self.debug('saving table to {}'.format(path))
        self._workbook = xlsxwriter.Workbook(add_extension(path, '.xlsx'), {'nan_inf_to_errors': True})
        self._bold = self._workbook.add_format({'bold': True})

        if unknowns:
            self._make_unknowns(unknowns)

        if airs:
            self._make_airs(airs)

        if blanks:
            self._make_blanks(blanks)

        if monitors:
            self._make_monitors(monitors)

        self._workbook.close()

    def _make_unknowns(self, unks):
        self._make_sheet(unks, 'Unknowns')

    def _make_airs(self, airs):
        self._make_sheet(airs, 'Airs')

    def _make_blanks(self, blanks):
        self._make_sheet(blanks, 'Blanks')

    def _make_monitors(self, monitors):
        self._make_sheet(monitors, 'Monitors')

    def _make_sheet(self, groups, name):
        self._current_row = 1

        worksheet = self._workbook.add_worksheet(name)

        self._format_worksheet(worksheet)

        self._make_title(worksheet, name)

        cols = self._get_columns(name)

        for group in groups:
            self._make_meta(worksheet, group)

            self._make_column_header(worksheet, cols)
            n = len(group.analyses) - 1
            for i, item in enumerate(group.analyses):
                self._make_analysis(worksheet, cols, item, i == n)
            self._make_summary(worksheet, cols, group)
            self._current_row += 1

        self._make_notes(worksheet, len(cols), name)
        self._current_row = 1

    def _format_worksheet(self, sh):
        if self._options.hide_gridlines:
            sh.hide_gridlines(2)

    def _make_title(self, sh, name):

        fmt = self._workbook.add_format({'font_size': 14, 'bold': True,
                                         'bottom': 6})
        sh.write_rich_string(self._current_row, 0, 'Table X. {}'.format(name), fmt)

        cols = self._get_columns(name)
        for i in xrange(1, len(cols)):
            sh.write_blank(self._current_row, i, '', cell_format=fmt)
        self._current_row += 1

    def _make_column_header(self, sh, cols):
        names = [c[1] for c in cols]
        units = [c[2] for c in cols]

        superscript = self._workbook.add_format({'font_script': 1})
        subscript = self._workbook.add_format({'font_script': 2})

        border = self._workbook.add_format({'bottom': 2})
        start = 9
        sh.write(self._current_row, start, 'Corrected')
        sh.write(self._current_row, start + 10, 'Intercepts')
        sh.write(self._current_row, start + 20, 'Blanks')
        self._current_row += 1
        for items, use_border in ((names, False), (units, True)):
            row = self._current_row
            for i, ci in enumerate(items):
                if isinstance(ci, tuple):
                    args = []
                    for cii in ci:
                        for reg, fmt in ((supreg, superscript),
                                         (subreg, subscript)):
                            m = reg.match(cii)
                            if m:
                                args.append(fmt),
                                args.append(m.group('item'))
                                break
                        else:
                            args.append(cii)
                    if use_border:
                        args.append(border)
                    sh.write_rich_string(row, i, *args)
                else:
                    if use_border:
                        sh.write(row, i, ci, border)
                    else:
                        sh.write(row, i, ci)

            self._current_row += 1

    def _make_meta(self, sh, group):
        fmt = self._bold
        row = self._current_row
        sh.write_rich_string(row, 0, 'Sample:', fmt)
        sh.write_rich_string(row, 1, group.sample, fmt)

        sh.write_rich_string(row, 4, 'Identifier:', fmt)
        sh.write_rich_string(row, 5, group.identifier, fmt)

        self._current_row += 1

        row = self._current_row
        sh.write_rich_string(row, 0, 'Material:', fmt)
        sh.write_rich_string(row, 1, group.material, fmt)
        self._current_row += 1

    def _make_analysis(self, sh, cols, item, last):
        status = 'X' if item.tag != 'ok' else ''
        row = self._current_row

        border = self._workbook.add_format({'bottom': 1})
        fmt = []
        if last:
            fmt = [border]

        sh.write(row, 0, status, *fmt)
        for j, c in enumerate(cols[1:]):
            attr = c[3]
            if len(c) == 5:
                getter = c[4]
            else:
                getter = getattr

            txt = getter(item, attr)

            sh.write(row, j + 1, txt, *fmt)

        self._current_row += 1

    def _make_summary(self, sh, cols, group):
        idx = next((i for i, c in enumerate(cols) if c[1] == 'Age'))

        fmt = self._bold
        sh.write_rich_string(self._current_row, 0, u'Weight Mean Age {}'.format(PLUSMINUS_ONE_SIGMA), fmt)
        sh.write(self._current_row, idx, nominal_value(group.weighted_age))
        sh.write(self._current_row, idx + 1, std_dev(group.weighted_age))

        self._current_row += 1

        if self._options.include_plateau_age and hasattr(group, 'plateau_age'):
            sh.write_rich_string(self._current_row, 0, u'Plateau {}'.format(PLUSMINUS_ONE_SIGMA), fmt)
            sh.write(self._current_row, 2, 'steps {}'.format(group.plateau_steps_str))
            sh.write(self._current_row, idx, nominal_value(group.plateau_age))
            sh.write(self._current_row, idx + 1, std_dev(group.plateau_age))

            self._current_row += 1
        if self._options.include_isochron_age:
            sh.write_rich_string(self._current_row, 0, u'Isochron Age {}'.format(PLUSMINUS_ONE_SIGMA),
                                 fmt)
            sh.write(self._current_row, idx, nominal_value(group.isochron_age))
            sh.write(self._current_row, idx + 1, std_dev(group.isochron_age))

            self._current_row += 1

        if self._options.include_integrated_age and hasattr(group, 'integrated_age'):
            sh.write_rich_string(self._current_row, 0, u'Integrated Age {}'.format(PLUSMINUS_ONE_SIGMA),
                                 fmt)
            sh.write(self._current_row, idx, nominal_value(group.integrated_age))
            sh.write(self._current_row, idx + 1, std_dev(group.integrated_age))

            self._current_row += 1

    def _make_notes(self, sh, ncols, name):
        top = self._workbook.add_format({'top': 1})
        sh.write_rich_string(self._current_row, 0, 'Notes:', top)
        for i in xrange(1, ncols):
            sh.write_blank(self._current_row, i, 'Notes:', cell_format=top)
        self._current_row += 1

        func = getattr(self, '_make_{}_notes'.format(name.lower()))
        func(sh)

        for i in xrange(0, ncols):
            sh.write_blank(self._current_row, i, 'Notes:', cell_format=top)

    def _make_unknowns_notes(self, sh):
        monitor_age = 28.201
        decay_ref = u'Steiger and J\u00E4ger (1977)'
        for line in ('Isotopic ratios corrected for blank, radioactive decay, and mass discrimination, not corrected '
                     'for interfering reactions.',
                     'Errors quoted for individual analyses include analytical error only, without interfering '
                     'reaction or J uncertainties.',
                     'Integrated age calculated by summing isotopic measurements of all steps.',
                     'Plateau age is inverse-variance-weighted mean of selected steps.',
                     'Plateau age error is inverse-variance-weighted mean error (Taylor, 1982) times root MSWD where '
                     'MSWD>1.',
                     'Plateau error is weighted error of Taylor (1982).',
                     u'Decay constants and isotopic abundances after {}.'.format(decay_ref),
                     'X symbol preceding sample ID denotes analyses excluded from plateau age calculations.',
                     'Ages calculated relative to FC-2 Fish Canyon Tuff sanidine interlaboratory standard at '
                     '{} Ma '.format(monitor_age)):
            sh.write(self._current_row, 0, line)
            self._current_row += 1

    def _make_blanks_notes(self, sh):
        pass

    def _make_airs_notes(self, sh):
        pass

    def _make_monitor_notes(self, sh):
        pass


if __name__ == '__main__':
    x = XLSXTableWriter()


    class Iso:
        def __init__(self, name):
            self.name = name
            self.uvalue = 0
            self.blank = Blank(name)

        def get_intensity(self):
            return 0


    class Blank:
        def __init__(self, name):
            self.name = name
            self.uvalue = 0

        def get_intensity(self):
            return 0


    class A:
        isotopes = {'Ar40': Iso('Ar40'),
                    'Ar39': Iso('Ar39'),
                    'Ar38': Iso('Ar38'),
                    'Ar37': Iso('Ar37'),
                    'Ar36': Iso('Ar36')}
        tag = 'ok'
        aliquot_step_str = '01'
        extract_value = 0
        kca = 0
        age = 0
        age_err_wo_j = 0
        discrimination = 0
        j = 0

        ar39decayfactor = 0
        ar37decayfactor = 0
        interference_corrections = {}
        production_ratios = {}
        uF = 0
        rad40_percent = 54

        def __init__(self, a):
            self.aliquot_step_str = a

        def get_ic_factor(self, det):
            return 1
            # def __getattr__(self, item):
            #     return 0


    class G:
        sample = 'MB-1234'
        material = 'Groundmass'
        identifier = '13234'
        analyses = [A('01'), A('02')]
        weighted_age = 10.01
        plateau_age = 123
        integrated_age = 1231
        plateau_steps_str = 'A-F'


    g = G()
    p = '/Users/ross/Sandbox/testtable.xlsx'
    x.build(p, [g, g])
    app_path = '/Applications/Microsoft Office 2011/Microsoft Excel.app'

    try:
        subprocess.call(['open', '-a', app_path, p])
    except OSError:
        subprocess.call(['open', p])
# ============= EOF =============================================
