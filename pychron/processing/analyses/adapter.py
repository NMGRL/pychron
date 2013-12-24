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

from pychron.core.ui.text_table import TextTableAdapter, BoldCell, TextCell, TextRow, \
    TextTable, SimpleTextTableAdapter, HeaderRow
from pychron.core.helpers.formatting import errorfmt, floatfmt, pfloatfmt, \
    calc_percent_error
from pychron.pychron_constants import PLUSMINUS, SIGMA
#============= standard library imports ========================
#============= local library imports  ==========================
PLUSMINUS_SIGMA = u'{}1{}'.format(PLUSMINUS, SIGMA)


class RawAdapter(SimpleTextTableAdapter):
    columns = [
        ('Isotope', 'isotope', str),
        ('Detector', 'detector', str),
        ('Raw (fA)', 'raw_value'),
        (PLUSMINUS_SIGMA, 'raw_error'),
        (u'{}%  '.format(PLUSMINUS), 'raw_error_percent', str),
        ('Fit', 'fit', str),

        ('Baseline (fA)', 'baseline_value'),
        (PLUSMINUS_SIGMA, 'baseline_error'),
        (u'{}%  '.format(PLUSMINUS), 'baseline_error_percent', str),

        ('Blank (fA)', 'blank_value'),
        (PLUSMINUS_SIGMA, 'blank_error'),
        (u'{}%  '.format(PLUSMINUS), 'blank_error_percent', str),
    ]


class SignalAdapter(SimpleTextTableAdapter):
    columns = [
        ('Isotope', 'isotope', str),
        ('Detector', 'detector', str),
        ('Signal (fA)  ', 'signal_value'),
        (PLUSMINUS_SIGMA, 'signal_error'),
        ('Error Comp. %', 'error_component', pfloatfmt(n=1)),
        ('IC Factor', 'ic_factor_value'),
        (PLUSMINUS_SIGMA, 'ic_factor_error')
    ]


class AgeAdapter(TextTableAdapter):
    def _make_tables(self, record):
        age = record.age.nominal_value
        age_error = record.age.std_dev
        age_perror = calc_percent_error(age, age_error, n=3)
        woj_age_error = record.age_error_wo_j
        woj_age_perror = calc_percent_error(age, woj_age_error, n=3)

        ar40_39 = record.Ar40_39.nominal_value
        ar40_39_error = record.Ar40_39.std_dev
        ar40_39_perror = calc_percent_error(ar40_39, ar40_39_error, n=3)

        tt = TextTable(
            HeaderRow(TextCell(''), TextCell('Value'),
                      TextCell(u'{}1{}'.format(PLUSMINUS, SIGMA)),
                      TextCell('% error')
            ),
            TextRow(
                BoldCell('Age ({}):'.format(record.arar_constants.age_units)),
                TextCell(floatfmt(age)),
                TextCell(floatfmt(age_error)),
                TextCell(age_perror, n=2)
            ),
            TextRow(
                BoldCell('w/o J err:'),
                TextCell(''),
                TextCell(floatfmt(woj_age_error)),
                TextCell(woj_age_perror)
            ),
            TextRow(
                BoldCell('40Ar*/39Ar:'),
                TextCell(floatfmt(record.Ar40_39.nominal_value)),
                TextCell(floatfmt(record.Ar40_39.std_dev)),
                TextCell(ar40_39_perror),
                #                                HtmlCell('<sup>40</sup>Ar*/<sup>39</sup>Ar',
                #                                         bold=True)
            ),
            border=True
        )
        return [tt]


class AnalysisSummaryAdapter(TextTableAdapter):
    def _make_tables(self, record):
        info_table = self._make_info_table(record)
        return [info_table]

    def _keyword(self, args):
        kw = {}
        if len(args) == 3:
            name, value, kw = args
        else:
            name, value = args

        return BoldCell('{}:'.format(name)), TextCell(value, **kw)

    def _make_keyword_row(self, keys):
        cells = [ci for pairs in map(self._keyword, keys)
                 for ci in pairs]
        return TextRow(*cells)

    def _make_info_table(self, record):

        irrad = ''
        if record.irradiation:
            irrad = '{}{}'.format(record.irradiation,
                                  record.irradiation_level)

        j, je = record.j.nominal_value, record.j.std_dev
        flux = u'{} {}{}'.format(floatfmt(j), PLUSMINUS, errorfmt(j, je))
        sens = ''

        disc, disc_err = record.discrimination.nominal_value, record.discrimination.std_dev
        disc = u'{} {}{}'.format(floatfmt(disc), PLUSMINUS, errorfmt(disc, disc_err))

        tt = TextTable(
            self._make_keyword_row([('Analysis ID', record.record_id),
                                    ('Irradiation', irrad),
                                    ('Sample', record.sample),
            ]),
            self._make_keyword_row([('Comment',
                                     record.comment, {'col_span': -1})]),
            self._make_keyword_row(
                [('Date', record.rundate),
                 ('Time', record.runtime),
                 ('Disc.', disc),
                ]
            ),
            self._make_keyword_row(
                [('Spectrometer', record.mass_spectrometer),
                 ('Device', record.extract_device)]
            ),
            self._make_keyword_row([('Position', record.position),
                                    ('Extract ({})'.format(record.extract_units),
                                     record.extract_value),
                                    ('Duration (s)', record.extract_duration),
                                    ('Cleanup (s)', record.cleanup_duration)
            ]
            ),
            self._make_keyword_row([('J', flux, {'col_span': 2}),
                                    ('Sensitivity', sens, {'col_span': 2})
            ]),
            border=False
        )
        return tt

        #============= EOF =============================================
