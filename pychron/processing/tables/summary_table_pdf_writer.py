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
from traits.api import HasTraits, Int, Str
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pdf.base_pdf_writer import BasePDFWriter
from pychron.helpers.formatting import floatfmt
from pychron.pdf.items import Row, Subscript, Superscript, NamedParameter, \
    FootNoteRow, FooterRow
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
from pychron.paths import paths
import yaml

def DefaultInt(value=40):
    return Int(value)



class SummaryTablePDFWriter(BasePDFWriter):
    notes_template = Str('summary_table.temp')

    def _build(self, doc, samples, title):

        title_para = self._new_paragraph(title)
        flowables = [title_para, self._vspacer(0.1)]

#         t, t2 = self._make_table(samples)
        t = self._make_table(samples)
        flowables.append(t)
        flowables.append(self._vspacer(0.1))
#         flowables.append(t2)
#         n = self._make_notes()
#         flowables.append(n)

        return flowables, None

    def _short_material_name(self, mat):
        if mat.lower() == 'groundmass concentrate':
            mat = 'GMC'

        return mat

    def _make_table(self, samples):
        style = self._new_style(
#                                 debug_grid=True,
                                header_line_idx=1
                                )

        style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
        style.add('LEFTPADDING', (0, 0), (-1, -1), 1)
        self._new_line(style, 0, cmd='LINEABOVE')

        data = []

        # make meta
#         meta = self._make_meta(analyses, style)
#         data.extend(meta)
#
        # make header
        header = self._make_header(style)
        data.extend(header)

        cnt = len(data)
        for i, sam in enumerate(samples):

            r = self._make_sample_row(sam)
            data.append(r)

            if self.use_alternating_background:
                idx = cnt + i
                if i % 2 != 0:
                    style.add('BACKGROUND', (0, idx), (-1, idx),
                              colors.lightgrey,
                              )

#         for i, sam in enumerate(samples[:1]):
#
#             r = self._make_sample_row(sam)
#             data.append(r)
#
#             idx = cnt + i * 2
#             style.add('BACKGROUND', (0, idx), (-1, idx),
#                       colors.lightgrey,
#                       )

        idx = len(data) - 1
        self._new_line(style, idx)
#         s = self._make_summary_rows(means, idx + 1, style)
#         data.extend(s)

        self._make_notes(data, style)

        t = self._new_table(style, data,
                            repeatRows=3)

#         r = Row()
#         r.add_blank_item(10)
#         fdata = [r]
#         style = self._new_style()
#         style.add('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey)
#         self._make_footnote_rows(fdata, style)
#         self._make_footer_rows(fdata, style)
#         ft = self._new_table(style, fdata, extend_last=True)


        return t

    def _make_header(self, style):
        PMS = u'\u00b1 1\u03c3'


        pr = Row()
        pr.add_blank_item(6)
        pr.add_item(value='Preferred Age', span=-1)
#         style.add('ALIGN', (0, 3), (0, -1), 'CENTER')
        self._new_line(style, 0, weight=0.75, start=4, end=-1)

        r = Row()

        r.add_item(value='Sample')
        r.add_item(value='L#')
        r.add_item(value='Irrad')
        r.add_item(value='Material')

        r.add_item(value='Type')
        r.add_item(value='N')
        r.add_item(value='MSWD')
        r.add_item(value='K/Ca')
        r.add_item(value=PMS)
        r.add_item(value='Age')
        r.add_item(value=PMS)

        return (pr, r,)
#         sigma = u'\u00b1 1\u03c3'
# #         sigma = self._plusminus_sigma()
#         super_ar = lambda x: '{}Ar'.format(Superscript(x))
#
#         _102fa = '(10{} fA)'.format(Superscript(2))
#         _103fa = '(10{} fA)'.format(Superscript(3))
#         minus_102fa = '(10{} fA)'.format(Superscript(-2))
#
# #         blank = self._make_footnote('BLANK',
# #                                    'Blank Type', 'LR= Linear Regression, AVE= Average',
# #                                    'Blank')
# #         blank = 'Blank Type'
#         line = [
#                 ('', ''),
#                 ('N', ''),
#                 ('Power', '(%)'),
#                 (super_ar(40), ''),
#                 (super_ar(40), _103fa), (sigma, ''),
#                 (super_ar(39), _103fa), (sigma, ''),
#                 (super_ar(38), ''), (sigma, ''),
#                 (super_ar(37), ''), (sigma, ''),
#                 (super_ar(36), ''), (sigma, minus_102fa),
#                 ('%{}*'.format(super_ar(40)), ''),
#                 ('{}*/{}{}'.format(super_ar(40),
#                                    super_ar(39),
#                                    Subscript('K')), ''),
#                 ('Age', '(Ma)'), (sigma, ''),
#                 ('K/Ca', ''),
#                 (sigma, ''),
# #                 (blank, 'type'),
# #                 (super_ar(40), ''), (sigma, ''),
# #                 (super_ar(39), ''), (sigma, ''),
# #                 (super_ar(38), ''), (sigma, ''),
# #                 (super_ar(37), ''), (sigma, ''),
# #                 (super_ar(36), ''), (sigma, ''),
#               ]
#
#         name_row, unit_row = zip(*line)
#
#         default_fontsize = 8
#         nrow = Row(fontsize=default_fontsize)
#         for i, ni in enumerate(name_row):
#             nrow.add_item(value=ni)
#
#         default_fontsize = 7
#         urow = Row(fontsize=default_fontsize)
#         for ni in unit_row:
#             urow.add_item(value=ni)
#
#         name_row_idx = 2
#         unit_row_idx = 3
#         # set style for name header
#         style.add('LINEABOVE', (0, name_row_idx),
#                   (-1, name_row_idx), 1.5, colors.black)
#
#         # set style for unit header
#         style.add('LINEBELOW', (0, unit_row_idx),
#                   (-1, unit_row_idx), 1.5, colors.black)
#
#         return [
#                 nrow,
#                 urow
#                 ]

    def _make_sample_row(self, sample):
        row = Row()
        row.add_item(value=sample.sample)
        row.add_item(value=sample.identifier)
        row.add_item(value=sample.irradiation)
        row.add_item(value=self._short_material_name(sample.material))
        row.add_item(value=sample.age_type)
        row.add_item(value=sample.nanalyses)
        row.add_item(value=floatfmt(sample.mswd, n=1))
        row.add_item(value=self._value(n=1)(sample.weighted_kca))
        row.add_item(value=self._error(n=1)(sample.weighted_kca))
        row.add_item(value=self._value(n=4)(sample.weighted_age))
        row.add_item(value=self._error(n=4)(sample.weighted_age))

        return row


    def _set_row_heights(self, table, data):
        a_idxs = self._get_idxs(data, (FooterRow, FootNoteRow))
        for a, v in a_idxs:
            table._argH[a] = 0.19 * inch

        idx = self._get_idxs(data, Row)
        for i, v in idx:
            if v.height:
                table._argH[i] = v.height * inch

#===============================================================================
# summary
#===============================================================================
    def _make_notes(self, data, style):
        p = os.path.join(paths.template_dir, self.notes_template)

        if os.path.isfile(p):
            with open(p, 'r') as fp:
                meta = ''
                for li in fp:
                    if li.startswith('#-----------'):
                        break

                    meta += li
                meta = yaml.load(meta)
                txt = ''
                for li in fp:
                    txt += li

            size = meta.get('fontsize', 5)
            leading = meta.get('leading', 5)
            bgcolor = meta.get('bgcolor', None)

            p = self._new_paragraph(txt, leading=leading)
            r = Row(fontsize=size)
            r.add_item(value=p, span=-1)
            data.append(r)
            if bgcolor:
                bgcolor = bgcolor.replace(' ', '')
                if hasattr(colors, bgcolor):
                    idx = len(data) - 1
                    style.add('BACKGROUND', (0, idx), (-1, idx),
                          getattr(colors, bgcolor),
                          )

#===============================================================================
# footnotes
#===============================================================================
#     def _make_footnote_rows(self, data, style):
#         return
#
#         data.append(Row(height=0.1))
#         def factory(f):
#             r = FootNoteRow(fontsize=6)
#             r.add_item(value=f)
#             return r
#         data.extend([factory(fi) for fi in self._footnotes])
#
# #         _get_idxs = lambda x: self._get_idxs(rows, x)
#         _get_se = lambda x: (x[0][0], x[-1][0])
#         # set for footnot rows
#         footnote_idxs = self._get_idxs(data, FootNoteRow)
#         sidx, eidx = _get_se(footnote_idxs)
#         style.add('VALIGN', (0, sidx), (-1, eidx), 'MIDDLE')
#         for idx, _v in footnote_idxs:
#             style.add('SPAN', (0, idx), (-1, idx))
# #            style.add('VALIGN', (1, idx), (-1, idx), 'MIDDLE')

#===============================================================================
#
#===============================================================================

#============= EOF =============================================
# class TableSpec(HasTraits):
#     status_width = Int(5)
#     id_width = Int(20)
#     power_width = Int(30)
#     moles_width = Int(50)
#
#
#     ar40_width = DefaultInt(value=45)
#     ar40_error_width = DefaultInt()
#     ar39_width = DefaultInt(value=45)
#     ar39_error_width = DefaultInt()
#     ar38_width = DefaultInt()
#     ar38_error_width = DefaultInt()
#     ar37_width = DefaultInt()
#     ar37_error_width = DefaultInt()
#     ar36_width = DefaultInt()
#     ar36_error_width = DefaultInt(value=50)
