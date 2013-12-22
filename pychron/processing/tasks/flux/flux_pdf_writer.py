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
from reportlab.platypus.flowables import PageBreak

from pychron.loading.component_flowable import ComponentFlowable

#============= standard library imports ========================
#============= local library imports  ==========================
from itertools import groupby
from pychron.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.pdf.items import Row, Superscript, Subscript
from pychron.stats.core import calculate_weighted_mean
from pychron.helpers.formatting import floatfmt
from pychron.processing.argon_calculations import calculate_flux
class FluxPDFWriter(BasePDFTableWriter):
    monitor_age = 28.02e6
    def _build(self, doc, ans, component):

        flowables = [
                    ComponentFlowable(component=component),
                    PageBreak(),
                     ]
        ts = self._make_tables(ans)

        for i in range(len(ts) - 1, 0, -1):
            ts.insert(i, self._vspacer(0.25))

        flowables.extend(ts)
        templates = None
        return flowables, templates

    def _make_tables(self, tans):
        return [self._make_table(ln, ans)
                    for ln, ans in groupby(tans,
                                       lambda x: x.labnumber)]

    def _make_table(self, ln, ans):
        ans = list(ans)
        style = self._new_style(
                                header_line_idx=0,
#                                 debug_grid=True
                                )
        header = self._make_header()
        data = [header]

        ans = sorted(ans, key=lambda x:x.age)

        data.extend([self._make_analysis_row(ai) for ai in ans])
        idx = len(data) - 1
        self._new_line(style, idx)

        data.append(self._make_weighted_mean_row(ans))
        data.append(self._make_flux_row(ans))

        cs = [10, 40, 40, 40, 40, 60]
        return self._new_table(style, data,
                                col_widths=cs
                               )
    def _make_flux_row(self, ans):

        mR = sum(ai.R for ai in ans) / len(ans)
        j, e = calculate_flux(mR, 1, self.monitor_age)
        r = Row(fontsize=8)
        r.add_item(value='<b>J</b>', span=5)
        r.add_item(value='<b>{}</b>'.format(floatfmt(j)))
        r.add_item(value='<b>{}</b>'.format(floatfmt(e)))

        return r

    def _make_weighted_mean_row(self, ans):
        r = Row(fontsize=8)

        ages, errors = zip(*[(ai.age.nominal_value, ai.age.std_dev)
                            for ai in ans])

        wm, we = calculate_weighted_mean(ages, errors)
        r.add_item(value='<b>weighted mean</b>', span=2)
        r.add_blank_item(3)
        r.add_item(value='<b>{}</b>'.format(floatfmt(wm)))
        r.add_item(value=u'<b>\u00b1{}</b>'.format(floatfmt(we)))

        return r

    def _make_header(self):
        header = Row()
        S40 = Superscript('40')
        S39 = Superscript('39')
        sK = Subscript('K')
        attrs = (
               '', 'N', 'Power', 'Mol. {}Ar'.format(S40),
               '{}Ar*%'.format(S40),
                '{}Ar*/{}Ar{}'.format(S40, S39, sK),
               'Age', u'\u00b1 1\u03c3',
               'K/Ca', u'\u00b1 1\u03c3',
               )


        for a in attrs:
            header.add_item(value=u'<b>{}</b>'.format(a))

        return header
    def _make_analysis_row(self, analysis):
        value = self._value
        error = self._error
        attrs = [
                 ('temp_status', lambda x: '' if x == 0 else 'X'),
                 ('aliquot_step_str', '{}',),
                 ('extract_value', '{}'),
                 ('moles_Ar40', value()),
                 ('rad40_percent', value(n=1)),
                 ('F', value(n=5)),
                 ('age', value(n=2)),
                 ('age', error(n=4)),
                 ('kca', value(n=2)),
                 ('kca', error(n=2)),
                 ]

        return self._new_row(analysis, attrs)


#============= EOF =============================================
