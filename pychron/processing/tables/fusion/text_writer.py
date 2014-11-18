#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Bool, Instance, Enum
from uncertainties import nominal_value, std_dev

from pychron.loggable import Loggable





#============= standard library imports ========================
#============= local library imports  ==========================

def iso_value(attr, ve='value'):
    def f(x, k):
        if k in x.isotopes:
            iso = x.isotopes[k]
            if attr == 'intercept':
                v = iso.uvalue
            elif attr == 'baseline':
                v = iso.baseline.uvalue
            elif attr == 'disc_ic_corrected':
                v = iso.get_intensity()
            elif attr == 'interference_corrected':
                v = iso.get_interference_corrected_value()
            elif attr == 'blank':
                v = iso.blank.uvalue
        if v is not None:
            return nominal_value(v) if ve == 'value' else std_dev(v)
        else:
            return ''

    return f


def correction_value(ve='value'):
    def f(x, k):
        v = None
        if k in x.interference_corrections:
            v = x.interference_corrections[k]
        elif k in x.production_ratios:
            v = x.production_ratios[k]

        if v is not None:
            return nominal_value(v) if ve == 'value' else std_dev(v)
        else:
            return ''

    return f


def icf_value(x, k):
    det = k.split('_')[0]
    return nominal_value(x.get_ic_factor(det))


def icf_error(x, k):
    det = k.split('_')[0]
    return std_dev(x.get_ic_factor(det))


def value(x, k):
    x = getattr(x, k)
    if x:
        return nominal_value(x)
    else:
        return ''


def error(x, k):
    x = getattr(x, k)
    if x:
        return std_dev(x)
    else:
        return ''


class FusionTableTextOptions(HasTraits):
    use_sample_sheets = Bool(False)
    age_nsigma = Enum(2, 1, 3)
    kca_nsigma = Enum(2, 1, 3)


class LaserTableTextWriter(Loggable):
    options = Instance(FusionTableTextOptions, ())
    columns = (
        ('Status', 'status'),
        ('Labnumber', 'labnumber'),
        ('N', 'aliquot_step_str'),
        ('Sample', 'sample'),
        ('Material', 'material'),
        ('Irradiation', 'irradiation_label'),
        ('Power', 'extract_value'),

        #                     'Moles_40Ar',
        # interference corrected
        ('Ar40_interf', 'Ar40', iso_value('interference_corrected')),
        ('Ar40Er_interf', 'Ar40', iso_value('interference_corrected', ve='error')),
        ('Ar39_interf', 'Ar39', iso_value('interference_corrected')),
        ('Ar39Er_interf', 'Ar39', iso_value('interference_corrected', ve='error')),
        ('Ar38_interf', 'Ar38', iso_value('interference_corrected')),
        ('Ar38Er_interf', 'Ar38', iso_value('interference_corrected', ve='error')),
        ('Ar37_interf', 'Ar37', iso_value('interference_corrected')),
        ('Ar37Er_interf', 'Ar37', iso_value('interference_corrected', ve='error')),
        ('Ar36_interf', 'Ar36', iso_value('interference_corrected')),
        ('Ar36Er_interf', 'Ar36', iso_value('interference_corrected', ve='error')),

        # disc/ic corrected
        ('Ar40_disc_ic', 'Ar40', iso_value('disc_ic_corrected')),
        ('Ar40Er_disc_ic', 'Ar40', iso_value('disc_ic_corrected', ve='error')),
        ('Ar39_disc_ic', 'Ar39', iso_value('disc_ic_corrected')),
        ('Ar39Er_disc_ic', 'Ar39', iso_value('disc_ic_corrected', ve='error')),
        ('Ar38_disc_ic', 'Ar38', iso_value('disc_ic_corrected')),
        ('Ar38Er_disc_ic', 'Ar38', iso_value('disc_ic_corrected', ve='error')),
        ('Ar37_disc_ic', 'Ar37', iso_value('disc_ic_corrected')),
        ('Ar37Er_disc_ic', 'Ar37', iso_value('disc_ic_corrected', ve='error')),
        ('Ar36_disc_ic', 'Ar36', iso_value('disc_ic_corrected')),
        ('Ar36Er_disc_ic', 'Ar36', iso_value('disc_ic_corrected', ve='error')),

        # intercepts
        ('Ar40_int', 'Ar40', iso_value('intercept')),
        ('Ar40Er_int', 'Ar40', iso_value('intercept', ve='error')),
        ('Ar39_int', 'Ar39', iso_value('intercept')),
        ('Ar39Er_int', 'Ar39', iso_value('intercept', ve='error')),
        ('Ar38_int', 'Ar38', iso_value('intercept')),
        ('Ar38Er_int', 'Ar38', iso_value('intercept', ve='error')),
        ('Ar37_int', 'Ar37', iso_value('intercept')),
        ('Ar37Er_int', 'Ar37', iso_value('intercept', ve='error')),
        ('Ar36_int', 'Ar36', iso_value('intercept')),
        ('Ar36Er_int', 'Ar36', iso_value('intercept', ve='error')),

        # baselines
        ('Ar40_bs', 'Ar40', iso_value('baseline')),
        ('Ar40Er_bs', 'Ar40', iso_value('baseline', ve='error')),
        ('Ar39_bs', 'Ar39', iso_value('baseline')),
        ('Ar39Er_bs', 'Ar39', iso_value('baseline', ve='error')),
        ('Ar38_bs', 'Ar38', iso_value('baseline')),
        ('Ar38Er_bs', 'Ar38', iso_value('baseline', ve='error')),
        ('Ar37_bs', 'Ar37', iso_value('baseline')),
        ('Ar37Er_bs', 'Ar37', iso_value('baseline', ve='error')),
        ('Ar36_bs', 'Ar36', iso_value('baseline')),
        ('Ar36Er_bs', 'Ar36', iso_value('baseline', ve='error')),

        # blanks
        ('Ar40_bk', 'Ar40', iso_value('blank')),
        ('Ar40Er_bk', 'Ar40', iso_value('blank', ve='error')),
        ('Ar39_bk', 'Ar39', iso_value('blank')),
        ('Ar39Er_bk', 'Ar39', iso_value('blank', ve='error')),
        ('Ar38_bk', 'Ar38', iso_value('blank')),
        ('Ar38Er_bk', 'Ar38', iso_value('blank', ve='error')),
        ('Ar37_bk', 'Ar37', iso_value('blank')),
        ('Ar37Er_bk', 'Ar37', iso_value('blank', ve='error')),
        ('Ar36_bk', 'Ar36', iso_value('blank')),
        ('Ar36Er_bk', 'Ar36', iso_value('blank', ve='error')),

        ('K/Ca', 'kca', value),
        ('K/CaErr', 'kca', error),
        ('Age', 'age', value),
        ('AgeErrWoJ', 'age_err_wo_j', value),
        ('Disc', 'discrimination', value),
        ('DiscEr', 'discrimination', error),
        ('CDD_ICFactor', 'CDD_ic_factor', icf_value),
        ('CDD_ICFactorErr', 'CDD_ic_factor', icf_error),
        ('J', 'j', value),
        ('JEr', 'j', error),
        ('39ArDecay', 'ar39decayfactor', value),
        ('37ArDecay', 'ar37decayfactor', value),
        ('K4039', 'k4039', correction_value()),
        ('K4039_err', 'k4039', correction_value(ve='error')),
        ('K3839', 'k3839', correction_value()),
        ('K3839_err', 'k3839', correction_value(ve='error')),
        ('K3739', 'k3739', correction_value()),
        ('K3739_err', 'k3739', correction_value(ve='error')),
        ('Ca3937', 'ca3937', correction_value()),
        ('Ca3937_err', 'ca3937', correction_value(ve='error')),
        ('Ca3837', 'ca3837', correction_value()),
        ('Ca3837_err', 'ca3837', correction_value(ve='error')),
        ('Ca3637', 'ca3637', correction_value()),
        ('Ca3637_err', 'ca3637', correction_value(ve='error')),
        ('Cl3638', 'cl3638', correction_value()),
        ('Cl3638_err', 'cl3638', correction_value(ve='error')),
        ('Ca_K', 'Ca_K', correction_value()),
        ('Ca_K_err', 'Ca_K', correction_value(ve='error')),
        ('Cl_K ', 'Cl_K', correction_value()),
        ('Cl_K_err', 'Cl_K', correction_value(ve='error')),
    )
    default_style = None

    def build(self, p, iagroups, groups, use_summary_sheet=False, title=None):
        self.info('saving table to {}'.format(p))
        wb = self._new_workbook()
        options = self.options
        if options.use_sample_sheets:
            for gi in groups:
                # for sam, ais in self._group_samples(ans):
                sh = self._add_sample_sheet(wb, gi.sample)
                #                 ais = list(ais)

                #                 self._add_metadata(sh, ais[0])
                self._add_header_row(sh, 0)
                self._add_analyses(sh, gi.analyses, start=2)
        else:
            if use_summary_sheet:
                self._write_summary_sheet(wb, iagroups)

            sh = wb.add_sheet('ArArData')
            start = 2
            for i, gi in enumerate(groups):
                if i == 0:
                    self._add_header_row(sh, 0)

                self._add_analyses(sh, gi.all_analyses, start=start)
                start += len(gi.all_analyses) + 1

        wb.save(p)

    def _write_summary_sheet(self, wb, groups):
        def set_nsigma(nattr):
            def f(item, attr):
                return getattr(item, attr) * getattr(self.options,
                                                     '{}_nsigma'.format(nattr))

            return f

        sh = wb.add_sheet('Summary')
        cols = [('Sample', 'sample'),
                ('Identifier', 'identifier'),
                ('Irradiation', 'irradiation'),
                ('Material', 'material'),
                ('Age Type', 'age_kind'),
                ('MSWD', 'mswd'),
                ('N', 'nanalyses'),
                ('K/Ca', 'kca'),
                (u'{}\u03c3'.format(self.options.kca_nsigma),
                 'kca_err', set_nsigma('kca')),

                ('Age', 'age'),
                (u'{}\u03c3'.format(self.options.age_nsigma),
                 'age_err', set_nsigma('age')),
        ]
        start = 1
        self._add_summary_header_row(sh, cols)
        for i, gi in enumerate(groups):
            self._add_summary_row(sh, gi, i + start, cols)

    def _add_summary_header_row(self, sh, cols, start=0):
        s1, s2 = self._get_header_styles()
        for i, ci in enumerate(cols):
            sh.write(start, i, ci[0], style=s2)

    def _add_summary_row(self, sh, gi, row, cols):
        for j, c in enumerate(cols):
            attr = c[1]
            if len(c) == 3:
                getter = c[2]
            else:
                getter = getattr

            txt = getter(gi, attr)
            sh.write(row, j, txt, self.default_style)

    def _add_analyses(self, sheet, ans, start):
        for i, ai in enumerate(ans):
            self._add_analysis(sheet, i + start, ai)

    def _add_analysis(self, sheet, row, ai):

        status = 'X' if ai.tag != 'ok' else ''

        sheet.write(row, 0, status)
        for j, c in enumerate(self.columns[1:]):
            attr = c[1]
            if len(c) == 3:
                getter = c[2]
            else:
                getter = getattr

            txt = getter(ai, attr)

            sheet.write(row, j + 1, txt, self.default_style)

    # def _group_samples(self, ans):
    #     key = lambda x: x.sample
    #     return groupby(ans, key=key)


    #     def _add_metadata(self, sh, refans):
    #         for i, c in enumerate(('labnumber', 'sample', 'material')):
    #             sh.write(0, i, getattr(refans, c))
    #         for i, c in enumerate(('irradiation', 'irradiation_level')):
    #             sh.write(1, i, getattr(refans, c))

    def _add_sample_sheet(self, wb, sample):
        sh = wb.add_sheet(sample)
        return sh

    def _add_header_row(self, sheet, hrow=0):

        names = [c[0] for c in self.columns]

        s1, s2 = self._get_header_styles()
        c = 7
        for t in ('Interference Corrected Isotope Intensities',
                  'Disc/IC Corrected Isotope Intensities',
                  'Uncorrected Isotope Intercepts',
                  'Baselines',
                  'Blanks'):
            sheet.write(hrow, c, t, style=s1)
            sheet.merge(hrow, hrow, c, c + 9)
            c = c + 10

        # sheet.write(hrow, 7, 'Interference Corrected Isotope Intensities', style=s1)
        # sheet.merge(hrow, hrow, 7, 16)
        #
        # sheet.write(hrow, 17, 'Disc/IC Corrected Isotope Intensities', style=s1)
        # sheet.merge(hrow, hrow, 17, 26)
        #
        # sheet.write(hrow, 27, 'Uncorrected Isotope Intercepts', style=s1)
        # sheet.merge(hrow, hrow, 26, 34)
        #
        # sheet.write(hrow, 35, 'Baselines', style=s1)
        # sheet.merge(hrow, hrow, 35, 43)
        #
        # sheet.write(hrow, 44, 'Blanks', style=s1)
        # sheet.merge(hrow, hrow, 44, 52)

        for i, ci in enumerate(names):
            sheet.write(hrow + 1, i, ci, style=s2)

    def _get_header_styles(self):
        return None, None

#============= EOF =============================================
