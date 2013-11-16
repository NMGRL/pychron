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
from reportlab.lib import colors
from traits.api import Str

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pdf.base_pdf_writer import BasePDFWriter
from pychron.pdf.items import Superscript, Subscript, Row, NamedParameter


class TablePDFWriter(BasePDFWriter):
    extract_label = Str
    extract_units = Str

    def _build(self, doc, ans, groups, title):
        self.debug('build table {}'.format(title))
        title_para = self._new_paragraph(title)

        templates = None
        flowables = [title_para, self._vspacer(0.1)]

        n = len(groups) - 1
        for i, group in enumerate(groups):

            include_footnotes = i == n
            fs = self._make_table(group, include_footnotes=include_footnotes)
            for fi in fs:
                flowables.append(fi)
                flowables.append(self._vspacer(0.1))

            if i < n:
                flowables.append(self._vspacer(0.25))

        return flowables, templates

    #def _make_footnotes(self, ref, row):
    #    ics=self._get_ic_factor(ref)
    #    foot = self._make_footnote('IC',
    #                                'IC Factor',
    #                                'H1/CDD intercalibration',
    #                                '<b>IC</b>',
    #                                link_extra=u': {}'.format(ics))
    #    return foot,
    #    #row.add_item(value=foot, span=3)
    #

    def _get_ic_factor(self, ref):
        ic = (1, 0)
        if not isinstance(ic, tuple):
            ic = ic.nominal_value, ic.std_dev
        return u'{:0.3f} \u00b1{:0.4f}'.format(ic[0], ic[1])

    def _make_meta(self, analyses, style, include_footnotes=False):
        ref = analyses[0]
        j = ref.j

        #ic = ref.ic_factor
        ic = (1, 0)
        sample = ref.sample
        labnumber = ref.labnumber
        material = ref.material

        igsn = ''

        if not isinstance(j, tuple):
            j = j.nominal_value, j.std_dev

        line1 = Row(fontsize=8)
        line1.add_item(value=NamedParameter('Sample', sample), span=5)
        line1.add_item(value=NamedParameter('Lab #', labnumber), span=2)

        js = u'{:0.2E} \u00b1{:0.2E}'.format(j[0], j[1])
        line1.add_item(value=NamedParameter('J', js), span=4)

        ics = self._get_ic_factor(ref)

        if include_footnotes:
            foot = self._make_footnote('IC',
                                       'IC Factor',
                                       'H1/CDD intercalibration',
                                       '<b>IC</b>',
                                       link_extra=u': {}'.format(ics))
        else:
            ics = self._get_ic_factor(ref)
            foot = NamedParameter('IC', ics)

        line1.add_item(value=foot, span=3)

        line2 = Row(fontsize=8)
        line2.add_item(value=NamedParameter('Material', material), span=5)
        line2.add_item(value=NamedParameter('IGSN', igsn), span=2)

        #         self._sample_summary_row1 = line1
        #         self._sample_summary_row2 = line2
        title = False
        title_row = 0
        sample_row = 0
        if title:
            sample_row += 1

        style.add('LINEBELOW', (0, sample_row), (-1, sample_row), 1.5, colors.black)

        return [line1, line2]

    def _make_header(self, style):
        sigma = u'\u00b1 1\u03c3'
        #         sigma = self._plusminus_sigma()
        super_ar = lambda x: '{}Ar'.format(Superscript(x))

        _102fa = '(10{} fA)'.format(Superscript(2))
        _103fa = '(10{} fA)'.format(Superscript(3))
        minus_102fa = '(10{} fA)'.format(Superscript(-2))

        #         blank = self._make_footnote('BLANK',
        #                                    'Blank Type', 'LR= Linear Regression, AVE= Average',
        #                                    'Blank')
        #         blank = 'Blank Type'
        line = [
            ('', ''),
            ('N', ''),
            (self.extract_label, '({})'.format(self.extract_units)),
            (super_ar(40), ''),
            (super_ar(40), _103fa), (sigma, ''),
            (super_ar(39), _103fa), (sigma, ''),
            (super_ar(38), ''), (sigma, ''),
            (super_ar(37), ''), (sigma, ''),
            (super_ar(36), ''), (sigma, minus_102fa),
            ('Age', '(Ma)'), (sigma, ''),
            ('%{}*'.format(super_ar(40)), ''),
            ('{}*/{}{}'.format(super_ar(40),
                               super_ar(39),
                               Subscript('K')), ''),

            ('K/Ca', ''),
            (sigma, ''),
            #                 (blank, 'type'),
            #                 (super_ar(40), ''), (sigma, ''),
            #                 (super_ar(39), ''), (sigma, ''),
            #                 (super_ar(38), ''), (sigma, ''),
            #                 (super_ar(37), ''), (sigma, ''),
            #                 (super_ar(36), ''), (sigma, ''),
        ]

        name_row, unit_row = zip(*line)

        default_fontsize = 8
        nrow = Row(fontsize=default_fontsize)
        for i, ni in enumerate(name_row):
            nrow.add_item(value=ni)

        default_fontsize = 7
        urow = Row(fontsize=default_fontsize)
        for ni in unit_row:
            urow.add_item(value=ni)

        name_row_idx = 2
        unit_row_idx = 3
        # set style for name header
        style.add('LINEABOVE', (0, name_row_idx),
                  (-1, name_row_idx), 1.5, colors.black)

        # set style for unit header
        style.add('LINEBELOW', (0, unit_row_idx),
                  (-1, unit_row_idx), 1.5, colors.black)

        return [
            nrow,
            urow
        ]

    #============= EOF =============================================
