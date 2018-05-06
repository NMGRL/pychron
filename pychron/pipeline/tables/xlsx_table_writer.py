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
import re
from itertools import groupby
from operator import attrgetter

import xlsxwriter
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from traits.api import Instance, BaseStr, HasTraits
from uncertainties import nominal_value, std_dev, ufloat

from pychron.core.helpers.filetools import add_extension, view_file
from pychron.paths import paths
from pychron.pipeline.tables.base_table_writer import BaseTableWriter
from pychron.pipeline.tables.column import Column, EColumn, VColumn
from pychron.pipeline.tables.util import iso_value, value, error, icf_value, icf_error, correction_value, age_value
from pychron.pipeline.tables.xlsx_table_options import XLSXTableWriterOptions
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup, StepHeatAnalysisGroup
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, PLUSMINUS_NSIGMA
import six

subreg = re.compile(r'^<sub>(?P<item>[\w\(\)]+)</sub>')
supreg = re.compile(r'^<sup>(?P<item>[\w\(\)]+)</sup>')

DEFAULT_UNKNOWN_NOTES = ('Corrected: Isotopic intensities corrected for blank, baseline, radioactivity decay and '
                         'detector intercalibration, not for interfering reactions.',
                         'Intercepts: t-zero intercept corrected for detector baseline.',
                         'Time interval (days) between end of irradiation and beginning of analysis',

                         'X symbol preceding sample ID denotes analyses excluded from plateau age calculations.',)


class IntermediateAnalysis(HasTraits):
    def is_omitted(self):
        return False

    def get_value(self, attr):
        try:
            return getattr(self, attr)
        except AttributeError:
            print('sdfa', attr)
            return 0


class XLSXTableWriter(BaseTableWriter):
    _workbook = None
    _current_row = 0
    _bold = None
    _superscript = None
    _subscript = None

    _options = Instance(XLSXTableWriterOptions)

    def _new_workbook(self, path):
        self._workbook = xlsxwriter.Workbook(add_extension(path, '.xlsx'), {'nan_inf_to_errors': True})

    def build(self, groups, path=None, options=None):
        if options is None:
            options = XLSXTableWriterOptions()

        self._options = options
        if path is None:
            path = options.path
        self.debug('saving table to {}'.format(path))

        self._new_workbook(path)

        self._bold = self._workbook.add_format({'bold': True})
        self._superscript = self._workbook.add_format({'font_script': 1})
        self._subscript = self._workbook.add_format({'font_script': 2})

        unknowns = groups.get('unknowns')
        if unknowns:
            # make a human optimized table
            self._make_human_unknowns(unknowns)

            # make a machine optimized table
        munknowns = groups.get('machine_unknowns')
        if munknowns:
            self._make_machine_unknowns(munknowns)

        airs = groups.get('airs')
        if airs:
            self._make_airs(airs)

        blanks = groups.get('blanks')
        if blanks:
            self._make_blanks(blanks)

        monitors = groups.get('monitors')
        if monitors:
            self._make_monitors(monitors)

        # if not self._options.include_production_ratios:
        #     self._make_irradiations(unknowns)

        if self._options.include_summary_sheet:
            if unknowns:
                self._make_summary_sheet(unknowns)

        self._workbook.close()

        view = self._options.auto_view
        if not view:
            view = confirm(None, 'Table saved to {}\n\nView Table?'.format(path)) == YES

        if view:
            view_file(path, application='Excel')

    # private
    def _get_detectors(self, grps):
        detectors = {i.detector for g in grps
                     for a in g.analyses
                     for i in a.isotopes.values()}
        return detectors

    def _get_columns(self, name, grps):

        detectors = self._get_detectors(grps)

        options = self._options

        ubit = name in ('Unknowns', 'Monitor')
        bkbit = ubit and options.include_blanks
        ibit = options.include_intercepts

        kcabit = ubit and options.include_kca
        age_units = '({})'.format(options.age_units)
        age_func = age_value(options.age_units)

        columns = [Column(attr='status'),
                   Column(label='N', attr='aliquot_step_str'),
                   Column(label='Tag', attr='tag'),
                   Column(enabled=ubit, label='Power', units=options.power_units, attr='extract_value'),
                   Column(enabled=ubit, label='Age', units=age_units, attr='age', func=age_func),
                   EColumn(enabled=ubit, units=age_units, attr='age_err_wo_j', func=age_func),
                   VColumn(enabled=kcabit, label='K/Ca', attr='kca'),
                   EColumn(enabled=ubit, attr='kca'),
                   VColumn(enabled=ubit and options.include_radiogenic_yield,
                           label=('%', '<sup>40</sup>', 'Ar'),
                           units='(%)', attr='rad40_percent'),
                   VColumn(enabled=ubit and options.include_F,
                           label=('<sup>40</sup>', 'Ar*/', '<sup>39</sup>', 'Ar', '<sub>K</sub>'),
                           attr='uF'),
                   VColumn(enabled=ubit and options.include_k2o,
                           label=('K', '<sub>2</sub>', 'O'),
                           units='(wt. %)', attr='k2o'),
                   VColumn(enabled=ubit and options.include_isochron_ratios,
                           label=('<sup>39</sup>', 'Ar/', '<sup>40</sup>', 'Ar'),
                           attr='isochron3940'),
                   VColumn(enabled=ubit and options.include_isochron_ratios,
                           label=('<sup>36</sup>', 'Ar/', '<sup>40</sup>', 'Ar'),
                           attr='isochron3640')]

        self._signal_columns(columns, ibit, bkbit)
        self._intercalibration_columns(columns, detectors)
        self._run_columns(columns, ubit)

        if options.include_production_ratios:
            pr = self._get_irradiation_columns(ubit)
            columns.extend(pr)
        else:
            irr = [Column(enabled=ubit, label='Irradiation', attr='irradiation_label')]
            columns.extend(irr)

        return columns

    def _run_columns(self, columns, ubit):
        options = self._options
        columns.extend([Column(enabled=options.include_rundate, label='RunDate', attr='rundate'),
                        Column(enabled=options.include_time_delta,
                               label=(u'\u0394t', '<sup>3</sup>'),
                               units='(days)',
                               attr='decay_days'),
                        VColumn(enabled=ubit, label='J', attr='j'),
                        EColumn(enabled=ubit, attr='j'),
                        VColumn(enabled=ubit, label=('<sup>39</sup>', 'Ar Decay'), attr='ar39decayfactor'),
                        VColumn(enabled=ubit, label=('<sup>37</sup>', 'Ar Decay'), attr='ar37decayfactor')])

    def _intercalibration_columns(self, columns, detectors):
        disc = [VColumn(label='Disc', attr='discrimination'),
                EColumn(attr='discrimination')]
        columns.extend(disc)

        for det in detectors:
            tag = '{}_ic_factor'.format(det)
            columns.extend([Column(label=('IC', '<sup>{}</sup>'.format(det)), attr=tag, func=icf_value),
                            EColumn(attr=tag, func=icf_error)])

    def _signal_columns(self, columns, ibit, bkbit):
        isos = (('Ar', 40), ('Ar', 39), ('Ar', 38), ('Ar', 37), ('Ar', 36))
        for bit, tag in ((ibit, 'intercept'), (True, 'disc_ic_corrected'), (bkbit, 'blank')):
            cols = [c for iso, mass in isos
                    for c in (Column(enabled=bit, attr='{}{}'.format(iso, mass),
                                     label=('<sup>{}</sup>'.format(mass), iso),
                                     units='(fA)',
                                     func=iso_value(tag)),
                              EColumn(enabled=bit,
                                      attr='{}{}'.format(iso, mass),
                                      func=iso_value(tag, ve='error')))]
            columns.extend(cols)

    def _get_machine_columns(self, name, grps):
        options = self._options

        detectors = self._get_detectors(grps)

        ubit = name in ('Unknowns', 'Monitor')
        bkbit = ubit and options.include_blanks
        ibit = options.include_intercepts

        kcabit = ubit and options.include_kca
        age_units = '({})'.format(options.age_units)
        age_func = age_value(options.age_units)

        columns = [Column(attr='status'),
                   Column(label='Identifier', attr='identifier'),
                   Column(label='Sample', attr='sample'),
                   Column(label='Material', attr='material'),
                   Column(label='Project', attr='project'),
                   Column(label='Tag', attr='tag'),

                   Column(label='N', attr='aliquot_step_str'),
                   Column(enabled=ubit, label='Power',
                          units=options.power_units,
                          attr='extract_value'),

                   Column(enabled=ubit, label='Age', units=age_units, attr='age', func=age_func),
                   EColumn(enabled=ubit, units=age_units, attr='age_err_wo_j', func=age_func),
                   VColumn(enabled=kcabit, label='K/Ca', attr='kca'),
                   EColumn(enabled=ubit, attr='kca'),
                   VColumn(enabled=ubit and options.include_radiogenic_yield,
                           label=('%', '<sup>40</sup>', 'Ar'),
                           units='(%)', attr='rad40_percent'),
                   VColumn(enabled=ubit and options.include_F,
                           label=('<sup>40</sup>', 'Ar*/', '<sup>39</sup>', 'Ar', '<sub>K</sub>'),
                           attr='uF'),
                   VColumn(enabled=ubit and options.include_k2o,
                           label=('K', '<sub>2</sub>', 'O'),
                           units='(wt. %)',
                           attr='k2o'),
                   VColumn(enabled=ubit and options.include_isochron_ratios,
                           label=('<sup>39</sup>', 'Ar/', '<sup>40</sup>', 'Ar'),
                           attr='isochron3940'),
                   VColumn(enabled=ubit and options.include_isochron_ratios,
                           label=('<sup>36</sup>', 'Ar/', '<sup>40</sup>', 'Ar'),
                           attr='isochron3640')]

        self._signal_columns(columns, ibit, bkbit)
        self._intercalibration_columns(columns, detectors)
        self._run_columns(columns, ubit)

        if options.include_production_ratios:
            pr = self._get_irradiation_columns(ubit)
            columns.extend(pr)
        else:
            c = Column(enabled=ubit, label='Irradiation', attr='irradiation_label')
            columns.append(c)

        return columns

    def _get_irradiation_columns(self, ubit):

        cols = [c for (ai, am), (bi, bm), e in ((('Ar', 40), ('Ar', 39), 'K'),
                                                (('Ar', 38), ('Ar', 39), 'K'),
                                                (('Ar', 37), ('Ar', 39), 'K'),

                                                (('Ar', 39), ('Ar', 37), 'Ca'),
                                                (('Ar', 38), ('Ar', 37), 'Ca'),
                                                (('Ar', 36), ('Ar', 37), 'Ca'),

                                                (('Ar', 36), ('Ar', 38), 'Cl'),

                                                )
                for c in (Column(label=('(', '<sup>{}</sup>'.format(am),
                                        '{}/'.format(ai),
                                        '<sup>{}</sup>'.format(bm), '{})'.format(bm), '<sub>{}</sub>'.format(e)),
                                 attr='{}{}{}'.format(e, am, bm)),
                          EColumn(attr='{}{}{}'.format(e, am, bm)))]

        cols.extend([Column(label='Ca/K', attr='Ca_K', ),
                     EColumn(attr='Ca_K'),
                     Column(label='Cl/K ', attr='Cl_K', ),
                     EColumn(attr='Cl_K')])

        for c in cols:
            c.enabled = ubit
            if isinstance(c, EColumn):
                c.func = correction_value(ve='error')
            else:
                c.func = correction_value()

        return cols

    def _get_summary_columns(self):
        opt = self._options

        def get_kca_error(ag, *args):
            return std_dev(ag.weighted_kca) * opt.summary_kca_nsigma

        def get_preferred_age_kind(ag, *args):
            ret = ''
            if isinstance(ag, InterpretedAgeGroup):
                ret = ag.preferred_age_kind
            return ret

        def get_preferred_age(ag, *args):
            return nominal_value(ag.preferred_age)

        def get_preferred_age_error(ag, *args):
            return std_dev(ag.preferred_age) * opt.summary_age_nsigma

        is_step_heat = opt.table_kind == 'Step Heat'
        age_units = '({})'.format(opt.age_units)

        cols = [Column(enabled=opt.include_summary_sample, label='Sample', attr='sample'),
                Column(enabled=opt.include_summary_identifier, label='Identifier', attr='identifier'),
                Column(enabled=opt.include_summary_unit, label='Unit', attr='unit'),
                Column(enabled=opt.include_summary_location, label='Location', attr='location'),
                Column(enabled=opt.include_summary_irradiation, label='Irradiation', attr='irradiation_label'),
                Column(enabled=opt.include_summary_material, label='Material', attr='material'),

                Column(enabled=opt.include_summary_age, label='Age Type', func=get_preferred_age_kind),
                # Column(enabled=opt.include_summary_age, 'Age Type', '', 'preferred_age_kind'),

                Column(enabled=opt.include_summary_n, label='N', attr='nanalyses'),
                Column(enabled=opt.include_summary_percent_ar39, label=('%', '<sup>39</sup>', 'Ar'),
                       attr='percent_39Ar'),
                Column(enabled=opt.include_summary_mswd, label='MSWD', attr='mswd'),
                Column(enabled=opt.include_summary_kca, label='K/Ca', attr='weighted_kca', func=value),

                Column(enabled=opt.include_summary_kca,
                       label=PLUSMINUS_NSIGMA.format(opt.summary_kca_nsigma),
                       attr='weighted_kca',
                       func=get_kca_error),

                Column(enabled=opt.include_summary_age,
                       label='Age {}'.format(age_units),
                       func=get_preferred_age),

                Column(enabled=opt.include_summary_age,
                       label=PLUSMINUS_NSIGMA.format(opt.summary_age_nsigma),
                       func=get_preferred_age_error),

                Column(enabled=opt.include_summary_comments, label='Comments', attr='comments'),

                # Hidden Cols
                VColumn(label='WeightedMeanAge', attr='weighted_age'),
                EColumn(attr='weighted_age'),
                VColumn(label='ArithmeticMeanAge', attr='arith_age'),
                EColumn(attr='arith_age'),
                VColumn(label='IsochronAge', attr='isochron_age'),
                EColumn(attr='isochron_age'),
                VColumn(enabled=is_step_heat, label='PlateauAge', attr='plateau_age'),
                VColumn(enabled=is_step_heat, attr='plateau_age'),
                VColumn(enabled=is_step_heat, label='IntegratedAge', attr='integrated_age'),
                VColumn(enabled=is_step_heat, attr='integrated_age')]
        return cols

    def _make_human_unknowns(self, unks):
        self._make_sheet(unks, 'Unknowns')

    def _make_machine_unknowns(self, unks):
        self._make_machine_sheet(unks, 'Unknowns (Machine)')

    def _make_airs(self, airs):
        self._make_sheet(airs, 'Airs')

    def _make_blanks(self, blanks):
        self._make_sheet(blanks, 'Blanks')

    def _make_monitors(self, monitors):
        self._make_sheet(monitors, 'Monitors')

    def _make_summary_sheet(self, unks):
        self._current_row = 1
        sh = self._workbook.add_worksheet('Summary')
        self._format_generic_worksheet(sh)

        cols = self._get_summary_columns()
        cols = [c for c in cols if c.enabled]
        self._make_title(sh, 'Summary', cols)

        fmt = self._workbook.add_format({'bottom': 1, 'align': 'center'})
        sh.set_row(self._current_row, 5)
        self._current_row += 1

        idx = next((i for i, c in enumerate(cols) if c.label == 'Age Type'), 6)
        idx_e = next((i for i, c in enumerate(cols) if c.label == 'Age'), 12) + 1
        # sh.write_rich_string(self._current_row, idx, 'Preferred Age', border)
        sh.merge_range(self._current_row, idx, self._current_row, idx_e, 'Preferred Age', cell_format=fmt)

        # hide extra age columns
        for hidden in ('WeightedMeanAge', 'ArithmeticMeanAge', 'IsochronAge', 'PlateauAge', 'IntegratedAge'):
            hc = next((i for i, c in enumerate(cols) if c.label == hidden), None)
            if hc is not None:
                sh.set_column(hc, hc + 1, options={'hidden': True})

        self._current_row += 1
        sh.set_row(self._current_row, 5)
        self._current_row += 1
        self._write_header(sh, cols, include_units=False)
        center = self._workbook.add_format({'align': 'center'})
        for ug in unks:
            ug.set_temporary_age_units(self._options.age_units)
            for i, ci in enumerate(cols):
                txt = self._get_txt(ug, ci)
                sh.write(self._current_row, i, txt, center)
            self._current_row += 1
            ug.set_temporary_age_units(None)

        self._make_notes(sh, len(cols), 'summary')

    # def _make_irradiations(self, unks):
    #     self._current_row = 1
    #     sh = self._workbook.add_worksheet('Irradiations')
    #     self._format_generic_worksheet(sh)
    #
    #     cols = [Column(label='Name', attr='irradiation')]
    #     icols = self._get_irradiation_columns(True)
    #     cols.extend(icols)
    #
    #     # write header
    #     self._write_header(sh, cols, include_units=True)
    #
    #     # cols = [c for c in cols if c.enabled]
    #     self._hide_columns(sh, cols)
    #     for ug in unks:
    #         for i, ci in enumerate(cols):
    #             try:
    #                 txt = self._get_txt(ug.analyses[0], ci)
    #             except AttributeError as e:
    #                 txt = self._get_txt(ug, ci)
    #
    #             sh.write(self._current_row, i, txt)
    #         self._current_row += 1

    def _make_sheet(self, groups, name):
        self._current_row = 1

        worksheet = self._workbook.add_worksheet(name)

        cols = self._get_columns(name, groups)
        self._format_worksheet(worksheet, cols)

        self._make_title(worksheet, name, cols)

        repeat_header = self._options.repeat_header

        for i, group in enumerate(groups):
            group.set_temporary_age_units(self._options.age_units)

            self._make_meta(worksheet, group)
            if repeat_header or i == 0:
                self._make_column_header(worksheet, cols, i)

            n = len(group.analyses) - 1
            nitems = []
            has_subgroups = False
            key = attrgetter('subgroup')
            ans = group.analyses
            for tg, items in groupby(ans, key=key):
                items = list(items)
                for i, item in enumerate(items):
                    ounits = item.arar_constants.age_units
                    item.arar_constants.age_units = self._options.age_units
                    self._make_analysis(worksheet, cols, item, i == n)
                if tg:
                    kind = '_'.join(tg.split('_')[:-1])
                    ia = self._make_intermediate_summary(worksheet, cols, items, kind)
                    nitems.append(ia)
                    has_subgroups = True
                else:
                    nitems.extend(items)

                for item in items:
                    item.arar_constants.age_units = ounits

            if has_subgroups:
                group.analyses = nitems

            self._make_summary(worksheet, cols, group)
            self._current_row += 1

            group.set_temporary_age_units(None)

        self._make_notes(worksheet, len(cols), name)
        self._current_row = 1

    def _make_machine_sheet(self, groups, name):
        self._current_row = 1
        worksheet = self._workbook.add_worksheet(name)

        cols = self._get_machine_columns(name, groups)
        self._format_worksheet(worksheet, cols)

        self._make_title(worksheet, name, cols)

        repeat_header = self._options.repeat_header

        for i, group in enumerate(groups):
            if repeat_header or i == 0:
                self._make_column_header(worksheet, cols, i)

            n = len(group.analyses) - 1
            for i, item in enumerate(group.analyses):
                self._make_analysis(worksheet, cols, item, i == n)
            self._current_row += 1

        self._current_row = 1

    def _format_generic_worksheet(self, sh):
        if self._options.hide_gridlines:
            sh.hide_gridlines(2)

    def _format_worksheet(self, sh, cols):
        self._format_generic_worksheet(sh)
        if self._options.include_rundate:
            idx = next((i for i, c in enumerate(cols) if c.label == 'RunDate'))
            sh.set_column(idx, idx, 12)

        sh.set_column(0, 0, 2)
        if not self._options.repeat_header:
            sh.freeze_panes(7, 2)
        self._hide_columns(sh, cols)

    def _hide_columns(self, sh, cols):
        for i, c in enumerate(cols):
            if not c.enabled:
                sh.set_column(i, i, options={'hidden': True})

    def _make_title(self, sh, name, cols):
        try:
            title = getattr(self._options, '{}_title'.format(name.lower()[:-1]))
        except AttributeError:
            title = None

        fmt = self._workbook.add_format({'font_size': 14, 'bold': True,
                                         'bottom': 6 if not title else 0})
        sh.write_rich_string(self._current_row, 0, 'Table X. {}'.format(name), fmt)
        if title:
            self._current_row += 1
            sh.write_rich_string(self._current_row, 0, title)

        for i in range(1, len(cols)):
            sh.write_blank(self._current_row, i, '', cell_format=fmt)
        self._current_row += 1

    def _make_column_header(self, sh, cols, it):

        start = next((i for i, c in enumerate(cols) if c.attr == 'Ar40'), 9)

        if self._options.repeat_header and it > 0:
            sh.write(self._current_row, start, 'Corrected')
            sh.write(self._current_row, start + 10, 'Intercepts')
        else:
            sh.write_rich_string(self._current_row, start, 'Corrected', self._superscript, '1')
            sh.write_rich_string(self._current_row, start + 10, 'Intercepts', self._superscript, '2')

        sh.write(self._current_row, start + 20, 'Blanks')
        self._current_row += 1
        self._write_header(sh, cols)

    def _write_header(self, sh, cols, include_units=True):
        names, units = self._get_names_units(cols)

        border = self._workbook.add_format({'bottom': 2, 'align': 'center'})
        center = self._workbook.add_format({'align': 'center'})
        if include_units:
            t = ((names, False), (units, True))
        else:
            t = ((names, True),)

        for items, use_border in t:
            row = self._current_row
            for i, ci in enumerate(items):
                if isinstance(ci, tuple):
                    args = []
                    for cii in ci:
                        for reg, fmt in ((supreg, self._superscript),
                                         (subreg, self._subscript)):
                            m = reg.match(cii)
                            if m:
                                args.append(fmt),
                                args.append(m.group('item'))
                                break
                        else:
                            args.append(cii)

                    if not use_border:
                        args.append(center)
                    else:
                        args.append(border)
                    sh.write_rich_string(row, i, *args)
                else:
                    if use_border:
                        # border.set_align('center')
                        sh.write_rich_string(row, i, ci, border)
                    else:
                        sh.write_rich_string(row, i, ci, center)
            self._current_row += 1

    def _make_meta(self, sh, group):
        fmt = self._bold
        row = self._current_row
        sh.write_rich_string(row, 1, 'Sample:', fmt)
        sh.write_rich_string(row, 2, group.sample, fmt)

        sh.write_rich_string(row, 5, 'Identifier:', fmt)
        sh.write_rich_string(row, 6, group.identifier, fmt)

        self._current_row += 1

        row = self._current_row
        sh.write_rich_string(row, 1, 'Material:', fmt)
        sh.write_rich_string(row, 2, group.material, fmt)

        self._current_row += 1

    def _make_intermediate_summary(self, sh, cols, ans, kind):
        row = self._current_row
        ag = StepHeatAnalysisGroup(analyses=[ai for ai in ans if not ai.is_omitted()])
        age_idx = next((i for i, c in enumerate(cols) if c.label == 'Age'), 0)
        fmt = self._get_number_format('subgroup')
        fmt.set_bottom(1)

        fmt2 = self._workbook.add_format({'bottom': 1, 'bold': True})

        if kind == 'weighted_mean':
            a = ag.weighted_age
            label = 'wt. mean'
        elif kind == 'plateau':
            a = ag.plateau_age
            label = 'plateau'
        elif kind == 'isochron':
            a = ag.isochron_age
            label = 'isochron'
        elif kind == 'integrated':
            a = ag.integrated_age
        elif kind == 'plateau_else_weighted_mean':
            a = ag.plateau_age
            if not ag.plateau_steps:
                a = ag.weighted_age

        ia = IntermediateAnalysis()
        ia.uage = a
        ia.age_units = ag.age_units
        ia.age_scalar = ag.age_scalar
        ia.kca = kca = ag.weighted_kca
        ia.uage_wo_j_err = a

        ia.irradiation_label = ans[0].irradiation_label
        ia.irradiation = ans[0].irradiation
        ia.material = ans[0].material

        for i in range(age_idx + 1):
            sh.write_blank(row, i, '', fmt)

        sh.write_rich_string(row, 1, label, fmt2)

        if kind == 'plateau' and not ag.plateau_steps:
            a = None

        if a is not None:
            sh.write_number(row, age_idx, nominal_value(a), fmt)
            sh.write_number(row, age_idx + 1, std_dev(a), fmt)
        else:
            sh.write_number(row, age_idx, 'No plateau')

        sh.write_number(row, age_idx + 2, nominal_value(kca), fmt)
        sh.write_number(row, age_idx + 3, std_dev(kca), fmt)

        self._current_row += 1

        return ia

    def _get_number_format(self, kind=None):
        try:
            sf = getattr(self._options, '{}_sig_figs'.format(kind))
        except AttributeError:
            sf = self._options.sig_figs

        fn = self._workbook.add_format()
        fmt = '0.{}'.format('0' * (sf - 1))
        if not self._options.ensure_trailing_zeros:
            fmt = '{}#'.format(fmt)
        fn.set_num_format(fmt)
        return fn

    def _make_analysis(self, sh, cols, item, last):
        status = 'X' if item.is_omitted() else ''
        row = self._current_row

        border = self._workbook.add_format({'bottom': 1})
        fmt2 = self._workbook.add_format()
        fmt3 = self._workbook.add_format()
        fmt_j = self._get_number_format('j')
        fmt = []

        fn = self._get_number_format()
        if last:
            fmt2 = self._workbook.add_format({'bottom': 1})
            fmt3 = self._workbook.add_format({'bottom': 1})
            fmt.append(border)
            fn.set_bottom(1)

        fmt2.set_align('center')
        fmt3.set_num_format('mm/dd/yy hh:mm')

        sh.write(row, 0, status, *fmt)
        for j, c in enumerate(cols[1:]):
            txt = self._get_txt(item, c)

            if c.label in ('N', 'Power'):
                sh.write(row, j + 1, txt, fmt2)
            elif c.label == 'RunDate':
                sh.write_datetime(row, j + 1, txt, fmt3)
            elif c.attr == 'j':
                sh.write_number(row, j + 1, txt, fmt_j)
            else:

                if isinstance(txt, float):
                    sh.write_number(row, j + 1, txt, cell_format=fn)
                else:
                    sh.write(row, j + 1, txt, *fmt)

        self._current_row += 1

    def _make_summary(self, sh, cols, group):
        nfmt = self._get_number_format('summary')
        fmt = self._bold
        start_col = 0
        if self._options.include_kca:
            idx = next((i for i, c in enumerate(cols) if c.label == 'K/Ca'))
            sh.write_rich_string(self._current_row, start_col, u'Weighted Mean K/Ca {}'.format(PLUSMINUS_ONE_SIGMA),
                                 fmt)
            kca = group.weighted_kca if self._options.use_weighted_kca else group.arith_kca
            sh.write_number(self._current_row, idx, nominal_value(kca), nfmt)
            sh.write_number(self._current_row, idx + 1, std_dev(kca), nfmt)
            self._current_row += 1

        idx = next((i for i, c in enumerate(cols) if c.label == 'Age'))

        sh.write_rich_string(self._current_row, start_col, u'Weighted Mean Age {}'.format(PLUSMINUS_ONE_SIGMA), fmt)
        sh.write_number(self._current_row, idx, nominal_value(group.weighted_age), nfmt)
        sh.write_number(self._current_row, idx + 1, std_dev(group.weighted_age), nfmt)

        sh.write_rich_string(self._current_row, idx + 2, 'n={}/{}'.format(group.nanalyses, group.total_n), fmt)

        self._current_row += 1
        if self._options.table_kind == 'Step Heat':
            if self._options.include_plateau_age and hasattr(group, 'plateau_age'):
                sh.write_rich_string(self._current_row, start_col, u'Plateau {}'.format(PLUSMINUS_ONE_SIGMA), fmt)
                sh.write(self._current_row, 3, 'steps {}'.format(group.plateau_steps_str))
                sh.write_number(self._current_row, idx, nominal_value(group.plateau_age), nfmt)
                sh.write_number(self._current_row, idx + 1, std_dev(group.plateau_age), nfmt)

                self._current_row += 1

            if self._options.include_integrated_age and hasattr(group, 'integrated_age'):
                sh.write_rich_string(self._current_row, start_col, u'Integrated Age {}'.format(PLUSMINUS_ONE_SIGMA),
                                     fmt)
                sh.write_number(self._current_row, idx, nominal_value(group.integrated_age), nfmt)
                sh.write_number(self._current_row, idx + 1, std_dev(group.integrated_age), nfmt)

                self._current_row += 1

        if self._options.include_isochron_age:

            sh.write_rich_string(self._current_row, start_col, u'Isochron Age {}'.format(PLUSMINUS_ONE_SIGMA),
                                 fmt)
            iage = group.isochron_age
            if iage is None:
                v, e = 0, 0
            else:
                v, e = nominal_value(iage), std_dev(iage)
            sh.write_number(self._current_row, idx, v, nfmt)
            sh.write_number(self._current_row, idx + 1, e, nfmt)

            self._current_row += 1

    def _make_notes(self, sh, ncols, name):
        top = self._workbook.add_format({'top': 1})
        sh.write_rich_string(self._current_row, 0, self._bold, 'Notes:', top)
        for i in range(1, ncols):
            sh.write_blank(self._current_row, i, 'Notes:', cell_format=top)
        self._current_row += 1

        func = getattr(self, '_make_{}_notes'.format(name.lower()))
        func(sh)

        for i in range(0, ncols):
            sh.write_blank(self._current_row, i, 'Notes:', cell_format=top)

    def _make_summary_notes(self, sh):
        sh.write(self._current_row, 0, 'Plateau Criteria:')
        self._current_row += 1

        sh.write(self._current_row, 0, '\t\tN Steps= {}'.format(self._options.plateau_nsteps))
        self._current_row += 1

        sh.write(self._current_row, 0, '\t\tGas Fraction= {}'.format(self._options.plateau_gas_fraction))
        self._current_row += 1
        if self._options.fixed_step_low or self._options.fixed_step_high:
            sh.write(self._current_row, 0, '\t\tFixed Steps= {},{}'.format(self._options.fixed_step_low,
                                                                           self.fixed_step_high))
            self._current_row += 1

    def _make_unknowns_notes(self, sh):
        monitor_age = 28.201
        decay_ref = u'Steiger and J\u00E4ger (1977)'
        notes = six.text_type(self._options.unknown_notes)
        notes = notes.format(monitor_age=monitor_age, decay_ref=decay_ref)

        sh.write_rich_string(self._current_row, 0, self._superscript, '1', DEFAULT_UNKNOWN_NOTES[0])
        self._current_row += 1
        sh.write_rich_string(self._current_row, 0, self._superscript, '2', DEFAULT_UNKNOWN_NOTES[1])
        self._current_row += 1
        if self._options.include_time_delta:
            sh.write_rich_string(self._current_row, 0, self._superscript, '3', DEFAULT_UNKNOWN_NOTES[2])
            self._current_row += 1

        sh.write(self._current_row, 0, DEFAULT_UNKNOWN_NOTES[3])
        self._current_row += 1

        self._write_notes(sh, notes)

    def _make_blanks_notes(self, sh):
        notes = six.text_type(self._options.blank_notes)
        self._write_notes(sh, notes)

    def _make_airs_notes(self, sh):
        notes = six.text_type(self._options.air_notes)
        self._write_notes(sh, notes)

    def _make_monitor_notes(self, sh):
        notes = six.text_type(self._options.monitor_notes)
        self._write_notes(sh, notes)

    def _write_notes(self, sh, notes):
        for line in notes.split('\n'):
            sh.write(self._current_row, 0, line)
            self._current_row += 1

    def _get_names_units(self, cols):
        names = [c.label for c in cols]
        units = [c.units for c in cols]
        return names, units

    def _get_txt(self, item, col):
        attr = col.attr
        if attr is None:
            return ''

        # if len(col) == 5:
        #     getter = col[4]
        # else:
        #     getter = getattr

        func = col.func
        if func is None:
            func = getattr
        return func(item, attr)


if __name__ == '__main__':
    x = XLSXTableWriter()

    from random import random
    from datetime import datetime


    def frand(digits, scalar=1):
        return round(scalar * random(), digits)


    class Iso:
        def __init__(self, name):
            self.name = name
            self.uvalue = ufloat(frand(10, 10), frand(10))
            self.blank = Blank(name)
            self.detector = 'CDD'

        def get_intensity(self):
            return ufloat(frand(10, 10), frand(10))


    class Blank:
        def __init__(self, name):
            self.name = name
            self.uvalue = ufloat(frand(10, 1), frand(10))

        def get_intensity(self):
            return ufloat(frand(10, 1), frand(10))


    class AC:
        age_units = 'Ma'
        ma_age_scalar = 1


    class A:
        def is_omitted(self):
            return False

        def __init__(self, a):
            self.identifier = 'Foo'
            self.project = 'Bar'
            self.material = 'Moo'
            self.sample = 'Bat'
            self.aliquot_step_str = a
            self.isotopes = {'Ar40': Iso('Ar40'),
                             'Ar39': Iso('Ar39'),
                             'Ar38': Iso('Ar38'),
                             'Ar37': Iso('Ar37'),
                             'Ar36': Iso('Ar36')}
            self.arar_constants = AC()
            self.tag = 'ok'
            self.aliquot_step_str = '01'
            self.extract_value = frand(1)
            self.kca = ufloat(frand(2), frand(2))
            self.age = frand(10, 10)
            self.age_err_wo_j = frand(10)
            self.discrimination = 0
            self.j = 0

            self.ar39decayfactor = 0
            self.ar37decayfactor = 0
            self.interference_corrections = {}
            self.production_ratios = {'Ca_K': 1.312}
            self.uF = ufloat(frand(10, 10), frand(10))
            self.rad40_percent = frand(3, 100)
            self.rundate = datetime.now()
            self.decay_days = frand(2, 200)
            self.k2o = frand(2)
            self.irradiation_label = 'NM-284 E9'
            self.irradiation = 'NM-284'
            self.isochron3940 = ufloat(frand(10), frand(10))
            self.isochron3640 = ufloat(frand(10), frand(10))

        def get_ic_factor(self, det):
            return 1
            # def __getattr__(self, item):
            #     return 0


    class G:
        sample = 'MB-1234'
        material = 'Groundmass'
        identifier = '13234'
        analyses = [A('01'), A('02')]
        arith_age = 132
        weighted_age = 10.01
        plateau_age = 123
        integrated_age = 1231
        plateau_steps_str = 'A-F'
        isochron_age = 123323
        weighted_kca = 1412
        arith_kca = 0.123
        preferred_age = 1213.123
        unit = ''
        location = ''
        mswd = frand(10)
        irradiation_label = 'Foo'
        preferred_age_kind = 'Plateau'
        nanalyses = 2
        percent_39Ar = 0.1234
        total_n = 2
        comments = ''

        def set_temporary_age_units(self, *args):
            pass


    g = G()
    p = '/Users/ross/Sandbox/testtable.xlsx'
    paths.build('_dev')
    options = XLSXTableWriterOptions()
    options.configure_traits()
    x.build(groups={'unknowns': [g, g],
                    'machine_unknowns': [g, g]},
            path=p, options=options)
    options.dump()
    # app_path = '/Applications/Microsoft Office 2011/Microsoft Excel.app'
    #
    # try:
    #     subprocess.call(['open', '-a', app_path, p])
    # except OSError:
    #     subprocess.call(['open', p])
# ============= EOF =============================================
