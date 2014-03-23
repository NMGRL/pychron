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
from traits.api import HasTraits, Bool, Instance
from uncertainties import nominal_value, std_dev

from pychron.loggable import Loggable

#============= standard library imports ========================
#============= local library imports  ==========================
class FusionTableTextOptions(HasTraits):
    use_sample_sheets = Bool(True)


def _getattr(x, k):
    if k in x.isotopes:
        v = x.isotopes[k].get_intensity()
    else:
        v = getattr(x, k)
    return v


def icf_value(x, k):
    det = k.split('_')[0]
    return nominal_value(x.get_ic_factor(det))


def icf_error(x, k):
    det = k.split('_')[0]
    return std_dev(x.get_ic_factor(det))


def value(x, k):
    x = _getattr(x, k)
    if x:
        return nominal_value(x)
    else:
        return ''


def error(x, k):
    x = _getattr(x, k)
    if x:
        return std_dev(x)
    else:
        return ''


def blank_value(x, k):
    if k in x.isotopes:
        x = x.isotopes[k]
        return x.blank.uvalue.nominal_value
    else:
        return ''


def blank_error(x, k):
    if k in x.isotopes:
        x = x.isotopes[k]
        return x.blank.uvalue.std_dev
    else:
        return ''


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
        ('Ar40', 'Ar40', value),
        ('Ar40Er', 'Ar40', error),
        ('Ar39', 'Ar39', value),
        ('Ar39Er', 'Ar39', error),
        ('Ar38', 'Ar38', value),
        ('Ar38Er', 'Ar38', error),
        ('Ar37', 'Ar37', value),
        ('Ar37Er', 'Ar37', error),
        ('Ar36', 'Ar36', value),
        ('Ar36Er', 'Ar36', error),

        # blanks
        ('Ar40', 'Ar40', blank_value),
        ('Ar40Er', 'Ar40', blank_error),
        ('Ar39', 'Ar39', blank_value),
        ('Ar39Er', 'Ar39', blank_error),
        ('Ar38', 'Ar38', blank_value),
        ('Ar38Er', 'Ar38', blank_error),
        ('Ar37', 'Ar37', blank_value),
        ('Ar37Er', 'Ar37', blank_error),
        ('Ar36', 'Ar36', blank_value),
        ('Ar36Er', 'Ar36', blank_error),
        ('K/Ca', 'kca', value),
        ('K/CaErr', 'kca', error),
        ('Age', 'age', value),
        ('AgeErrWoJ', 'age_err_wo_j', value),
        ('Disc', 'discrimination', value),
        ('DiscEr', 'discrimination', error),
        ('CDD_ICFactor', 'CDD_ic_factor', icf_value),
        ('CDD_ICFactorErr', 'CDD_ic_factor', icf_error)

    )
    default_style = None

    def build(self, p, groups, title=None):
        self.info('saving table to {}'.format(p))
        wb = self._new_workbook()
        options = self.options
        options.use_sample_sheets = False
        if options.use_sample_sheets:
            for gi in groups:
                # for sam, ais in self._group_samples(ans):
                sh = self._add_sample_sheet(wb, gi.sample)
                #                 ais = list(ais)

                #                 self._add_metadata(sh, ais[0])
                self._add_header_row(sh, 0)
                self._add_analyses(sh, gi.analyses, start=2)
        else:
            sh = wb.add_sheet('ArArData')
            start = 2
            for i, gi in enumerate(groups):
                if i == 0:
                    self._add_header_row(sh, 0)

                self._add_analyses(sh, gi.analyses, start=start)
                start += len(gi.analyses) + 1

        wb.save(p)

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
        sheet.write(hrow, 7, 'Corrected Isotope Intensities', style=s1)
        sheet.merge(hrow, hrow, 7, 16)
        sheet.write(hrow, 17, 'Blanks', style=s1)
        sheet.merge(hrow, hrow, 17, 27)

        for i, ci in enumerate(names):
            sheet.write(hrow + 1, i, ci, style=s2)

    def _get_header_styles(self):
        return None, None

#============= EOF =============================================
